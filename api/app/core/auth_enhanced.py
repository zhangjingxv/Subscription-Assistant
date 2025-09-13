"""
增强的认证系统
支持刷新令牌、账户安全、邮箱验证等功能
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import smtplib

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from passlib.context import CryptContext
from jose import JWTError, jwt
import structlog

from app.core.config import get_settings
from app.core.db import get_db
from app.core.exceptions import AuthenticationError, ValidationError
from app.models.user import User
from app.core.cache import cache_manager

logger = structlog.get_logger()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenManager:
    """JWT 令牌管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 7
        
    def create_token_pair(self, user_id: str) -> Dict[str, Any]:
        """创建访问令牌和刷新令牌对"""
        now = datetime.utcnow()
        
        # 访问令牌（短期）
        access_token_data = {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_minutes)
        }
        
        # 刷新令牌（长期）
        refresh_token_data = {
            "sub": str(user_id),
            "type": "refresh", 
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire_days)
        }
        
        access_token = jwt.encode(
            access_token_data,
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm
        )
        
        refresh_token = jwt.encode(
            refresh_token_data,
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "refresh_expires_in": self.refresh_token_expire_days * 24 * 60 * 60
        }
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            if payload.get("type") != token_type:
                return None
                
            return payload
        except JWTError:
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """使用刷新令牌获取新的访问令牌"""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # 检查用户是否仍然有效
        # 这里可以添加额外的验证逻辑
        
        # 创建新的访问令牌
        now = datetime.utcnow()
        access_token_data = {
            "sub": user_id,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_minutes)
        }
        
        access_token = jwt.encode(
            access_token_data,
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }


class AccountSecurity:
    """账户安全管理"""
    
    def __init__(self):
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self.password_min_length = 8
        
    async def check_account_locked(self, db: AsyncSession, user: User) -> bool:
        """检查账户是否被锁定"""
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True
        return False
    
    async def record_failed_login(self, db: AsyncSession, user: User):
        """记录登录失败"""
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= self.max_failed_attempts:
            user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
            logger.warning(
                "Account locked due to too many failed attempts",
                user_id=user.id,
                email=user.email,
                attempts=user.failed_login_attempts
            )
        
        await db.commit()
    
    async def record_successful_login(self, db: AsyncSession, user: User):
        """记录登录成功"""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        await db.commit()
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """验证密码强度"""
        if len(password) < self.password_min_length:
            return False, f"密码长度至少需要 {self.password_min_length} 位"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        strength_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength_score < 2:
            return False, "密码需要包含大写字母、小写字母、数字或特殊字符中的至少两种"
        
        return True, "密码强度符合要求"
    
    def generate_secure_token(self) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(32)


class EmailVerification:
    """邮箱验证管理"""
    
    def __init__(self):
        self.settings = get_settings()
        self.verification_expire_hours = 24
    
    def generate_verification_token(self, user_id: str, email: str) -> str:
        """生成邮箱验证令牌"""
        data = f"{user_id}:{email}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def send_verification_email(self, email: str, token: str, user_name: str = None):
        """发送验证邮件"""
        if not self.settings.smtp_host:
            logger.warning("SMTP not configured, skipping email verification")
            return
        
        try:
            verification_url = f"{self.settings.frontend_url}/verify-email?token={token}"
            
            msg = MimeMultipart()
            msg['From'] = self.settings.smtp_from_email
            msg['To'] = email
            msg['Subject'] = "验证您的 AttentionSync 账户"
            
            body = f"""
            <html>
            <body>
                <h2>欢迎使用 AttentionSync！</h2>
                <p>Hi {user_name or '用户'}，</p>
                <p>请点击下面的链接验证您的邮箱地址：</p>
                <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 14px 25px; text-align: center; text-decoration: none; display: inline-block; border-radius: 4px;">验证邮箱</a></p>
                <p>或者复制以下链接到浏览器：</p>
                <p>{verification_url}</p>
                <p>此链接将在24小时后失效。</p>
                <p>如果您没有注册 AttentionSync 账户，请忽略此邮件。</p>
                <br>
                <p>AttentionSync 团队</p>
            </body>
            </html>
            """
            
            msg.attach(MimeText(body, 'html'))
            
            server = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)
            if self.settings.smtp_use_tls:
                server.starttls()
            if self.settings.smtp_username:
                server.login(self.settings.smtp_username, self.settings.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info("Verification email sent", email=email)
            
        except Exception as e:
            logger.error("Failed to send verification email", error=str(e), email=email)
            raise
    
    async def verify_email_token(self, db: AsyncSession, token: str) -> Optional[User]:
        """验证邮箱令牌"""
        query = select(User).where(User.email_verification_token == token)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # 检查令牌是否过期
        if user.created_at < datetime.utcnow() - timedelta(hours=self.verification_expire_hours):
            return None
        
        # 验证成功
        user.email_verified = True
        user.email_verification_token = None
        user.verified_at = datetime.utcnow()
        
        await db.commit()
        return user


class PasswordReset:
    """密码重置管理"""
    
    def __init__(self):
        self.settings = get_settings()
        self.reset_expire_hours = 2
        
    async def initiate_password_reset(self, db: AsyncSession, email: str) -> bool:
        """发起密码重置"""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # 为了安全，即使用户不存在也返回成功
            return True
        
        # 生成重置令牌
        reset_token = secrets.token_urlsafe(32)
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=self.reset_expire_hours)
        
        await db.commit()
        
        # 发送重置邮件
        await self._send_reset_email(user.email, reset_token, user.display_name)
        
        return True
    
    async def _send_reset_email(self, email: str, token: str, user_name: str):
        """发送密码重置邮件"""
        if not self.settings.smtp_host:
            logger.warning("SMTP not configured, skipping password reset email")
            return
        
        try:
            reset_url = f"{self.settings.frontend_url}/reset-password?token={token}"
            
            msg = MimeMultipart()
            msg['From'] = self.settings.smtp_from_email
            msg['To'] = email
            msg['Subject'] = "重置您的 AttentionSync 密码"
            
            body = f"""
            <html>
            <body>
                <h2>密码重置请求</h2>
                <p>Hi {user_name}，</p>
                <p>我们收到了您的密码重置请求。请点击下面的链接重置您的密码：</p>
                <p><a href="{reset_url}" style="background-color: #f44336; color: white; padding: 14px 25px; text-align: center; text-decoration: none; display: inline-block; border-radius: 4px;">重置密码</a></p>
                <p>或者复制以下链接到浏览器：</p>
                <p>{reset_url}</p>
                <p>此链接将在2小时后失效。</p>
                <p>如果您没有请求重置密码，请忽略此邮件。您的密码不会被更改。</p>
                <br>
                <p>AttentionSync 团队</p>
            </body>
            </html>
            """
            
            msg.attach(MimeText(body, 'html'))
            
            server = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)
            if self.settings.smtp_use_tls:
                server.starttls()
            if self.settings.smtp_username:
                server.login(self.settings.smtp_username, self.settings.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info("Password reset email sent", email=email)
            
        except Exception as e:
            logger.error("Failed to send password reset email", error=str(e), email=email)
            raise
    
    async def reset_password(self, db: AsyncSession, token: str, new_password: str) -> bool:
        """重置密码"""
        query = select(User).where(
            User.password_reset_token == token,
            User.password_reset_expires > datetime.utcnow()
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # 验证新密码强度
        security = AccountSecurity()
        is_valid, message = security.validate_password_strength(new_password)
        if not is_valid:
            raise ValidationError(message)
        
        # 更新密码
        user.hashed_password = pwd_context.hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.last_password_change = datetime.utcnow()
        
        # 重置登录失败计数
        user.failed_login_attempts = 0
        user.locked_until = None
        
        await db.commit()
        
        logger.info("Password reset successfully", user_id=user.id, email=user.email)
        return True


# 全局实例
token_manager = TokenManager()
account_security = AccountSecurity()
email_verification = EmailVerification()
password_reset = PasswordReset()


async def get_current_user_enhanced(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """增强的当前用户获取（支持缓存）"""
    
    # 验证访问令牌
    payload = token_manager.verify_token(credentials.credentials, "access")
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # 尝试从缓存获取用户信息
    cache_key = f"user:{user_id}"
    cached_user = await cache_manager.get(cache_key)
    
    if cached_user:
        # 反序列化用户对象
        user = User(**cached_user)
        return user
    
    # 从数据库查询
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("User account is disabled")
    
    # 检查账户是否被锁定
    if await account_security.check_account_locked(db, user):
        raise AuthenticationError("Account is temporarily locked")
    
    # 缓存用户信息（5分钟）
    user_dict = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "email_verified": user.email_verified
    }
    await cache_manager.set(cache_key, user_dict, ttl=300)
    
    return user


# 可选的用户依赖（不要求认证）
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """可选的当前用户获取"""
    try:
        return await get_current_user_enhanced(credentials, db)
    except:
        return None