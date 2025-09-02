"""
Security configuration with proper secret management.
Following the kernel principle: "Never trust user input, always validate"
"""

import os
import secrets
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Manages secrets with proper validation.
    No hardcoded values, no magic strings.
    """
    
    @staticmethod
    def get_secret(key: str, default: Optional[str] = None) -> str:
        """
        Get a secret from environment or generate a secure one.
        Never return hardcoded defaults for sensitive values.
        """
        value = os.environ.get(key)
        
        if not value:
            if default and not SecretManager._is_placeholder(default):
                # Only use default if it's not a placeholder
                return default
            
            # Generate secure random secret if not provided
            if "KEY" in key or "SECRET" in key or "PASSWORD" in key:
                value = SecretManager._generate_secure_secret()
                logger.warning(
                    f"Generated random secret for {key}. "
                    f"Set {key} environment variable for production!"
                )
                return value
            
            # For non-sensitive values, use default
            return default or ""
        
        # Validate the secret is not a placeholder
        if SecretManager._is_placeholder(value):
            raise ValueError(
                f"Security Error: {key} contains placeholder value. "
                f"Set proper value in environment!"
            )
        
        return value
    
    @staticmethod
    def _is_placeholder(value: str) -> bool:
        """Check if value is a placeholder that shouldn't be used"""
        placeholders = [
            "your-secret-key-here",
            "your-jwt-secret-here",
            "changeme",
            "minioadmin",
            "admin",
            "password",
            "secret",
            "default",
            "test",
            "demo"
        ]
        return value.lower() in placeholders
    
    @staticmethod
    def _generate_secure_secret() -> str:
        """Generate a cryptographically secure secret"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_production_secrets(environment: str) -> None:
        """
        Validate that production has proper secrets.
        Fail fast, fail loud - Linus style.
        """
        if environment != "production":
            return
        
        required_secrets = [
            "SECRET_KEY",
            "JWT_SECRET",
            "DATABASE_URL",
            "POSTGRES_PASSWORD",
            "MINIO_ROOT_PASSWORD"
        ]
        
        missing = []
        insecure = []
        
        for key in required_secrets:
            value = os.environ.get(key)
            if not value:
                missing.append(key)
            elif SecretManager._is_placeholder(value):
                insecure.append(key)
        
        if missing:
            raise RuntimeError(
                f"Production requires these environment variables: {', '.join(missing)}"
            )
        
        if insecure:
            raise RuntimeError(
                f"Production has insecure placeholder values for: {', '.join(insecure)}"
            )
        
        logger.info("✅ Production secrets validated")


# Export singleton instance
secret_manager = SecretManager()
