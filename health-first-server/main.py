from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import config
from app.database.connections import db_manager
from app.api.provider_endpoints import router as provider_router
from app.api.auth_endpoints import router as auth_router
from app.api.protected_endpoints import router as protected_router
from app.api.availability_endpoints import router as availability_router
from app.api.patient_endpoints import router as patient_router
from app.api.patient_auth_endpoints import router as patient_auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not config.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.
    """
    # Startup
    logger.info("Starting Health First Provider Registration API")
    
    try:
        # Initialize database connections
        db_manager.initialize()
        if db_manager.is_initialized():
            logger.info(f"Database initialized successfully: {config.DATABASE_TYPE}")
        else:
            logger.warning("Database initialization failed, running with limited functionality")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        logger.info("Continuing without database - API will have limited functionality")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Health First Provider Registration API")
    
    try:
        # Close database connections
        db_manager.close_connections()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Create FastAPI application
app = FastAPI(
    title=config.APP_NAME,
    description="Secure provider and patient registration system with authentication, supporting SQL and NoSQL databases",
    version=config.VERSION,
    docs_url="/docs",  # Always enable for development
    redoc_url="/redoc",  # Always enable for development
    lifespan=lifespan
)

# Add CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(provider_router)
app.include_router(auth_router)
app.include_router(protected_router)
app.include_router(availability_router)
app.include_router(patient_router)
app.include_router(patient_auth_router)

# Root endpoint
@app.get("/", tags=["Health Check"])
async def root():
    """
    Health check endpoint.
    """
    return JSONResponse(
        status_code=200,
        content={
            "message": f"Welcome to {config.APP_NAME}",
            "version": config.VERSION,
            "status": "healthy",
            "database_type": config.DATABASE_TYPE,
            "database_connected": db_manager.is_initialized(),
            "features": [
                "Provider Registration",
                "Patient Registration",
                "JWT Authentication", 
                "Multi-Database Support",
                "Comprehensive Validation",
                "Security Middleware",
                "HIPAA Compliance"
            ],
            "endpoints": {
                "provider_registration": "/api/v1/provider/register",
                "patient_registration": "/api/v1/patient/register",
                "login": "/api/v1/provider/login",
                "protected_demo": "/api/v1/provider/profile",
                "docs": "/docs"
            }
        }
    )

# Health check endpoint
@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Detailed health check endpoint.
    """
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "version": config.VERSION,
            "database_type": config.DATABASE_TYPE,
            "database_connected": db_manager.is_initialized(),
            "timestamp": "2024-01-01T00:00:00Z"  # In real app, use actual timestamp
        }
        
        # Test database connectivity if initialized
        if db_manager.is_initialized():
            if config.DATABASE_TYPE == "mongodb":
                try:
                    collection = db_manager.get_providers_collection()
                    collection.find_one()
                    health_status["database_status"] = "connected"
                except Exception as e:
                    health_status["database_status"] = f"error: {str(e)}"
                    health_status["status"] = "degraded"
            else:
                try:
                    with db_manager.get_sql_session() as session:
                        session.execute(text("SELECT 1"))
                    health_status["database_status"] = "connected"
                except Exception as e:
                    health_status["database_status"] = f"error: {str(e)}"
                    health_status["status"] = "degraded"
        else:
            health_status["database_status"] = "not initialized"
            health_status["status"] = "degraded"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
        log_level="info" if not config.DEBUG else "debug"
    ) 