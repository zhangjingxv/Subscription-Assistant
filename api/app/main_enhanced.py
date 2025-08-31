"""
AttentionSync Enhanced API - Linus style: intelligent adaptation
"The best software adapts to reality, rather than demanding reality adapt to it."
"""

import os
import time
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.smart_deps import initialize_smart_dependencies
from app.routers import smart_api

# Configure enhanced logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class IntelligentRateLimiter:
    """Intelligent rate limiter - adapts based on system load"""
    
    def __init__(self):
        self.requests = {}
        self.base_limit = 100
        self.current_limit = self.base_limit
        
    def adapt_limit_based_on_load(self):
        """Adapt rate limit based on system performance"""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent()
            
            if cpu_usage > 80:
                self.current_limit = max(20, self.base_limit // 4)  # Reduce load
            elif cpu_usage > 60:
                self.current_limit = max(50, self.base_limit // 2)
            else:
                self.current_limit = self.base_limit  # Normal operation
                
        except ImportError:
            self.current_limit = self.base_limit
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed - adaptive limits"""
        self.adapt_limit_based_on_load()
        
        now = time.time()
        
        # Clean old entries
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if now - req_time < 60
            ]
        else:
            self.requests[client_ip] = []
        
        # Check adaptive limit
        if len(self.requests[client_ip]) >= self.current_limit:
            logger.warning(
                "Rate limit exceeded", 
                client_ip=client_ip,
                current_limit=self.current_limit,
                request_count=len(self.requests[client_ip])
            )
            return False
        
        self.requests[client_ip].append(now)
        return True


@asynccontextmanager
async def enhanced_lifespan(app: FastAPI):
    """Enhanced lifespan with intelligent dependency management"""
    logger.info("🚀 AttentionSync Enhanced API starting...")
    
    # Initialize smart dependency system
    try:
        feature_flags = await initialize_smart_dependencies()
        
        enabled_features = [k for k, v in feature_flags.items() if v]
        disabled_features = [k for k, v in feature_flags.items() if not v]
        
        logger.info(
            "🎯 Feature initialization complete",
            enabled=enabled_features,
            disabled=disabled_features
        )
        
        if disabled_features:
            logger.info("💡 To enable more features, install optional dependencies:")
            
            # Show specific install commands
            from app.core.smart_deps import get_dependency_manager
            manager = get_dependency_manager()
            commands = manager.generate_install_commands()
            
            for group, command in commands.items():
                logger.info(f"  {group}: {command}")
        
    except Exception as e:
        logger.error("⚠️  Dependency initialization failed", error=str(e))
        logger.info("🔄 Continuing with basic functionality...")
    
    logger.info("🎉 AttentionSync Enhanced API ready")
    yield
    
    logger.info("👋 AttentionSync Enhanced API shutting down gracefully")


def create_enhanced_app() -> FastAPI:
    """Create enhanced FastAPI app with intelligent features"""
    
    app = FastAPI(
        title="AttentionSync Enhanced API",
        description="智能自适应版本 - 按需功能加载",
        version="1.0.0-enhanced",
        lifespan=enhanced_lifespan
    )
    
    # Intelligent rate limiter
    rate_limiter = IntelligentRateLimiter()
    
    # Enhanced security middleware
    @app.middleware("http")
    async def intelligent_security_middleware(request: Request, call_next):
        """Intelligent security - adapts to system state"""
        
        client_ip = request.client.host if request.client else "unknown"
        
        # Adaptive rate limiting
        if not rate_limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded (current limit: {rate_limiter.current_limit}/min)"
            )
        
        # Request size validation
        content_length = request.headers.get("content-length")
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > 10:  # 10MB limit
                raise HTTPException(status_code=413, detail="Request too large")
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time
        
        # Add enhanced security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "X-Response-Time": f"{processing_time:.3f}s",
            "X-Rate-Limit": str(rate_limiter.current_limit),
            "X-Powered-By": "AttentionSync-Enhanced"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Log slow requests
        if processing_time > 1.0:
            logger.warning(
                "Slow request detected",
                path=request.url.path,
                method=request.method,
                processing_time=processing_time,
                client_ip=client_ip
            )
        
        return response
    
    # CORS with intelligent origins
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Add production origins if in production
    if os.getenv("ENVIRONMENT") == "production":
        prod_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        allowed_origins.extend([origin.strip() for origin in prod_origins if origin.strip()])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )
    
    # Health endpoints
    @app.get("/health")
    async def health():
        """Enhanced health check"""
        return {
            "status": "healthy",
            "service": "attentionsync-enhanced",
            "timestamp": time.time(),
            "rate_limit": rate_limiter.current_limit
        }
    
    @app.get("/health/system")
    async def system_health():
        """System health with intelligent monitoring"""
        try:
            import psutil
            process = psutil.Process()
            
            system_info = {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "open_files": process.num_fds(),
                "threads": process.num_threads(),
            }
            
            # Determine system status
            status = "healthy"
            warnings = []
            
            if system_info["cpu_percent"] > 80:
                status = "stressed"
                warnings.append("High CPU usage")
            
            if system_info["memory_mb"] > 200:
                status = "stressed" 
                warnings.append("High memory usage")
            
            return {
                "status": status,
                "warnings": warnings,
                "system": system_info,
                "rate_limit": {
                    "current": rate_limiter.current_limit,
                    "base": rate_limiter.base_limit,
                    "adaptive": rate_limiter.current_limit != rate_limiter.base_limit
                }
            }
            
        except ImportError:
            return {
                "status": "limited",
                "message": "System monitoring unavailable (install psutil for full monitoring)"
            }
    
    # Include smart API router
    app.include_router(smart_api.router, prefix="/api/v1", tags=["smart"])
    
    # Root endpoint with feature discovery
    @app.get("/")
    async def root():
        """Root endpoint with intelligent feature discovery"""
        from app.core.smart_deps import get_dependency_manager
        
        manager = get_dependency_manager()
        feature_flags = manager.create_feature_flags()
        enabled_count = sum(feature_flags.values())
        
        return {
            "service": "AttentionSync Enhanced API",
            "version": "1.0.0-enhanced",
            "philosophy": [
                "简洁性胜过复杂性",
                "安全性内建于架构", 
                "实用主义导向"
            ],
            "features": {
                "enabled": enabled_count,
                "total": len(feature_flags),
                "details": feature_flags
            },
            "endpoints": {
                "health": "/health",
                "features": "/api/v1/features/status",
                "smart_processing": "/api/v1/process/smart",
                "feature_installation": "/api/v1/features/install/{group}"
            }
        }
    
    return app


# Create enhanced app
app = create_enhanced_app()


if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.info("Using system environment (python-dotenv not available)")
    
    logger.info("🔒 Starting AttentionSync Enhanced API...")
    
    # Intelligent host binding
    environment = os.getenv("ENVIRONMENT", "development")
    host = "127.0.0.1" if environment == "development" else "0.0.0.0"
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🌐 Binding to {host}:{port} (environment: {environment})")
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,  # Disable for stability
            log_level="info",
            access_log=environment == "development"
        )
    except KeyboardInterrupt:
        logger.info("👋 Graceful shutdown")
    except Exception as e:
        logger.error("💥 Startup failed", error=str(e))
        sys.exit(1)