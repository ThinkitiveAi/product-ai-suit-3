from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
import logging

from app.middleware.auth_middleware import (
    get_current_provider,
    require_verified_provider,
    require_verified_and_active_provider
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/provider", tags=["Protected Provider Operations"])

@router.get(
    "/profile",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_provider)],
    responses={
        200: {
            "description": "Provider profile information",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Profile retrieved successfully",
                        "data": {
                            "provider_id": "uuid-here",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john.doe@clinic.com",
                            "specialization": "Cardiology",
                            "verification_status": "verified",
                            "is_active": True
                        }
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing token"
        }
    }
)
async def get_provider_profile(current_provider: Dict[str, Any] = Depends(get_current_provider)):
    """
    Get provider profile information.
    
    **Authentication Required:**
    - Valid JWT token in Authorization header
    - Any authenticated provider can access this endpoint
    
    **Usage Example:**
    ```
    curl -H "Authorization: Bearer <your-jwt-token>" \\
         http://localhost:8000/api/v1/provider/profile
    ```
    
    This endpoint demonstrates basic authentication middleware usage.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Profile retrieved successfully",
            "data": current_provider
        }
    )

@router.get(
    "/verified-only",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Verified provider content",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Access granted to verified provider",
                        "data": {
                            "verification_status": "verified",
                            "special_content": "This content is only available to verified providers"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing token"
        },
        403: {
            "description": "Forbidden - Provider not verified"
        }
    }
)
async def verified_provider_only(current_provider: Dict[str, Any] = Depends(require_verified_provider)):
    """
    Content accessible only by verified providers.
    
    **Authorization Required:**
    - Valid JWT token in Authorization header
    - Provider account must be verified (verification_status = "verified")
    
    **Usage Example:**
    ```
    curl -H "Authorization: Bearer <your-jwt-token>" \\
         http://localhost:8000/api/v1/provider/verified-only
    ```
    
    This endpoint demonstrates authorization middleware that requires
    the provider to be verified.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Access granted to verified provider",
            "data": {
                "verification_status": current_provider["verification_status"],
                "provider_id": current_provider["provider_id"],
                "special_content": "This content is only available to verified providers",
                "access_level": "verified"
            }
        }
    )

@router.get(
    "/premium-features",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Premium features for verified and active providers",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Premium features access granted",
                        "data": {
                            "features": [
                                "Advanced Analytics",
                                "Priority Support",
                                "Extended API Limits"
                            ]
                        }
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing token"
        },
        403: {
            "description": "Forbidden - Provider not verified or inactive"
        }
    }
)
async def premium_features(current_provider: Dict[str, Any] = Depends(require_verified_and_active_provider)):
    """
    Premium features accessible only by verified and active providers.
    
    **Authorization Required:**
    - Valid JWT token in Authorization header
    - Provider account must be verified AND active
    
    **Usage Example:**
    ```
    curl -H "Authorization: Bearer <your-jwt-token>" \\
         http://localhost:8000/api/v1/provider/premium-features
    ```
    
    This endpoint demonstrates advanced authorization middleware that requires
    multiple conditions to be met (verified AND active).
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Premium features access granted",
            "data": {
                "provider": {
                    "id": current_provider["provider_id"],
                    "email": current_provider["email"],
                    "specialization": current_provider["specialization"],
                    "verification_status": current_provider["verification_status"],
                    "is_active": current_provider["is_active"]
                },
                "features": [
                    "Advanced Analytics Dashboard",
                    "Priority Customer Support",
                    "Extended API Rate Limits",
                    "Custom Integrations",
                    "Advanced Reporting"
                ],
                "access_level": "premium",
                "expires": "Never (as long as account remains verified and active)"
            }
        }
    )

@router.post(
    "/update-profile",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Profile update successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Profile update initiated",
                        "data": {
                            "status": "pending",
                            "note": "Profile updates require admin approval"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing token"
        },
        403: {
            "description": "Forbidden - Provider not verified and active"
        }
    }
)
async def update_provider_profile(
    current_provider: Dict[str, Any] = Depends(require_verified_and_active_provider)
):
    """
    Update provider profile (demo endpoint).
    
    **Authorization Required:**
    - Valid JWT token in Authorization header
    - Provider account must be verified AND active
    
    **Usage Example:**
    ```
    curl -X POST \\
         -H "Authorization: Bearer <your-jwt-token>" \\
         -H "Content-Type: application/json" \\
         -d '{"update_field": "value"}' \\
         http://localhost:8000/api/v1/provider/update-profile
    ```
    
    This is a demo endpoint showing how to protect write operations
    with multiple authorization requirements.
    """
    logger.info(f"Profile update requested by provider: {current_provider['email']}")
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Profile update initiated",
            "data": {
                "status": "pending",
                "provider_id": current_provider["provider_id"],
                "note": "This is a demo endpoint. In a real application, this would update the provider's profile.",
                "current_verification": current_provider["verification_status"],
                "current_status": "active" if current_provider["is_active"] else "inactive"
            }
        }
    ) 