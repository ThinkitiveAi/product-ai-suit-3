from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

from app.schemas.auth import (
    ProviderLoginSchema,
    LoginSuccessResponseSchema,
    LoginErrorResponseSchema,
    TokenValidationSchema
)
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_provider, get_optional_current_provider

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/provider", tags=["Provider Authentication"])

# Initialize service
auth_service = AuthService()

@router.post(
    "/login",
    response_model=LoginSuccessResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Login successful",
            "model": LoginSuccessResponseSchema,
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Login successful",
                        "data": {
                            "access_token": "jwt-token-here",
                            "expires_in": 3600,
                            "token_type": "Bearer",
                            "provider": {
                                "provider_id": "uuid-here",
                                "email": "john.doe@clinic.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "specialization": "Cardiology",
                                "verification_status": "verified",
                                "is_active": True
                            }
                        }
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials",
            "model": LoginErrorResponseSchema,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_credentials": {
                            "summary": "Invalid email or password",
                            "value": {
                                "success": False,
                                "message": "Invalid credentials",
                                "error_code": "INVALID_CREDENTIALS"
                            }
                        },
                        "account_not_verified": {
                            "summary": "Account not verified",
                            "value": {
                                "success": False,
                                "message": "Account is not verified. Please verify your account first.",
                                "error_code": "ACCOUNT_NOT_VERIFIED"
                            }
                        },
                        "account_deactivated": {
                            "summary": "Account deactivated",
                            "value": {
                                "success": False,
                                "message": "Account is deactivated. Please contact support.",
                                "error_code": "ACCOUNT_DEACTIVATED"
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Validation failed",
                        "errors": {
                            "email": ["Invalid email format"],
                            "password": ["Password cannot be empty"]
                        }
                    }
                }
            }
        },
        500: {
            "description": "Server error",
            "model": LoginErrorResponseSchema
        }
    }
)
async def login_provider(login_data: ProviderLoginSchema):
    """
    Authenticate provider and generate JWT access token.
    
    This endpoint handles provider authentication with:
    - Email and password validation
    - Account status verification (active and verified)
    - JWT token generation with 1-hour expiry
    - Secure error handling without information leakage
    
    **Authentication Requirements:**
    - Valid email format
    - Non-empty password
    - Account must be verified and active
    
    **Token Information:**
    - Access token expires in 1 hour (3600 seconds)
    - Token type: Bearer
    - Contains provider information for authorization
    
    **Security Features:**
    - Passwords are never logged or exposed
    - Generic error messages prevent information leakage
    - Account status checks prevent unauthorized access
    - Token includes verification and active status
    
    **Error Codes:**
    - `INVALID_CREDENTIALS`: Wrong email or password
    - `ACCOUNT_NOT_VERIFIED`: Account needs verification
    - `ACCOUNT_DEACTIVATED`: Account is disabled
    - `AUTHENTICATION_ERROR`: Server-side authentication error
    """
    try:
        # Authenticate provider
        success, response_data = await auth_service.authenticate_provider(login_data)
        
        if success:
            logger.info(f"Successful login for: {login_data.email}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data
            )
        else:
            # Determine appropriate status code based on error
            error_code = response_data.get("error_code", "")
            
            if error_code in ["ACCOUNT_NOT_VERIFIED", "ACCOUNT_DEACTIVATED"]:
                status_code = status.HTTP_403_FORBIDDEN
            else:
                status_code = status.HTTP_401_UNAUTHORIZED
            
            logger.warning(f"Login failed for {login_data.email}: {response_data['message']}")
            return JSONResponse(
                status_code=status_code,
                content=response_data
            )
    
    except ValidationError as e:
        logger.warning(f"Login validation error: {str(e)}")
        error_details = {}
        
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            
            if field not in error_details:
                error_details[field] = []
            error_details[field].append(message)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation failed",
                "errors": error_details
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Authentication service temporarily unavailable",
                "error_code": "AUTHENTICATION_ERROR"
            }
        )

@router.get(
    "/verify-token",
    response_model=TokenValidationSchema,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Token validation result",
            "content": {
                "application/json": {
                    "examples": {
                        "valid_token": {
                            "summary": "Valid token",
                            "value": {
                                "valid": True,
                                "provider_id": "uuid-here",
                                "email": "john.doe@clinic.com",
                                "verification_status": "verified",
                                "is_active": True,
                                "expires_at": "2024-01-01T12:00:00Z"
                            }
                        },
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": {
                                "valid": False,
                                "error": "Invalid or expired token"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def verify_token(current_provider = Depends(get_optional_current_provider)):
    """
    Verify JWT access token validity.
    
    This endpoint validates the JWT token and returns token information:
    - Token validity status
    - Provider information if valid
    - Expiration details
    - Error information if invalid
    
    **Usage:**
    - Include JWT token in Authorization header: `Bearer <token>`
    - Returns validation status and provider info
    - Useful for frontend token validation
    
    **Token Validation:**
    - Signature verification
    - Expiration check
    - Provider existence check
    - Account status verification
    """
    try:
        if current_provider:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "valid": True,
                    "provider_id": current_provider["provider_id"],
                    "email": current_provider["email"],
                    "verification_status": current_provider["verification_status"],
                    "is_active": current_provider["is_active"],
                    "specialization": current_provider.get("specialization"),
                    "expires_at": None  # Would need to extract from token if needed
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "valid": False,
                    "error": "No valid token provided"
                }
            )
    
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "valid": False,
                "error": "Token verification failed"
            }
        )

@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Current provider information",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
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
async def get_current_provider_info(current_provider: Dict[str, Any] = Depends(get_current_provider)):
    """
    Get current authenticated provider information.
    
    This endpoint returns the current provider's profile information:
    - Requires valid JWT token in Authorization header
    - Returns complete provider profile (excluding sensitive data)
    - Useful for user profile displays and account management
    
    **Authentication Required:**
    - Valid JWT token in Authorization header
    - Account must be active
    
    **Response:**
    - Complete provider profile information
    - Excludes sensitive data like password hashes
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": current_provider
        }
    )

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Logout successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Logout successful"
                    }
                }
            }
        }
    }
)
async def logout_provider(current_provider: Dict[str, Any] = Depends(get_current_provider)):
    """
    Logout current provider.
    
    **Note:** Since JWT tokens are stateless, this endpoint primarily serves as a 
    confirmation of logout. The client should discard the token after calling this endpoint.
    
    In a production environment, you might want to implement token blacklisting
    or use refresh tokens for better security.
    
    **Authentication Required:**
    - Valid JWT token in Authorization header
    
    **Client Responsibility:**
    - Remove token from client storage after successful logout
    - Redirect to login page or public area
    """
    logger.info(f"Provider logged out: {current_provider['email']}")
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Logout successful"
        }
    ) 