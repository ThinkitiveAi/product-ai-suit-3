from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

from app.schemas.auth import (
    PatientLoginSchema,
    PatientLoginSuccessResponseSchema,
    LoginErrorResponseSchema,
    TokenValidationSchema
)
from app.schemas.patient import PatientResponseSchema
from app.services.patient_auth_service import PatientAuthService
from app.middleware.auth_middleware import get_current_patient, get_optional_current_patient

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/patient", tags=["Patient Authentication"])

# Initialize service
patient_auth_service = PatientAuthService()

@router.post(
    "/login",
    response_model=PatientLoginSuccessResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Login successful",
            "model": PatientLoginSuccessResponseSchema,
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Login successful",
                        "data": {
                            "access_token": "jwt-token-here",
                            "expires_in": 1800,  # 30 minutes in seconds
                            "token_type": "Bearer",
                            "patient": {
                                "patient_id": "uuid-here",
                                "email": "jane.smith@email.com",
                                "first_name": "Jane",
                                "last_name": "Smith",
                                "date_of_birth": "1990-05-15",
                                "gender": "female",
                                "email_verified": True,
                                "phone_verified": False,
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
async def login_patient(login_data: PatientLoginSchema):
    """
    Authenticate patient and return JWT access token.
    
    This endpoint allows patients to log in using their email and password.
    Upon successful authentication, a JWT token is returned with a 30-minute expiry.
    
    **Authentication Flow:**
    1. Validate email and password format
    2. Check if patient exists and password is correct
    3. Verify account is active (verification not required for login)
    4. Generate JWT token with patient information
    5. Return token and patient data (without sensitive information)
    
    **Token Information:**
    - Expiry: 30 minutes
    - Type: Bearer token
    - Payload includes: patient_id, email, role, verification status
    
    **Security Notes:**
    - Passwords are verified using secure hashing
    - Failed login attempts are logged for security monitoring
    - Account lockout mechanisms should be implemented for production
    """
    try:
        # Authenticate patient
        success, response_data = await patient_auth_service.authenticate_patient(login_data)
        
        if success:
            logger.info(f"Successful patient login: {login_data.email}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data
            )
        else:
            logger.warning(f"Failed patient login attempt: {login_data.email}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=response_data
            )
            
    except ValidationError as e:
        logger.warning(f"Validation error in patient login: {str(e)}")
        error_details = {}
        for error in e.errors():
            field = error["loc"][-1]
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
        logger.error(f"Unexpected error in patient login: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Login failed due to server error",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )

@router.post(
    "/validate-token",
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
                                "success": True,
                                "message": "Token is valid",
                                "data": {
                                    "valid": True,
                                    "patient_id": "uuid-here",
                                    "email": "jane.smith@email.com",
                                    "is_active": True,
                                    "email_verified": True,
                                    "phone_verified": False,
                                    "expires_at": 1234567890
                                }
                            }
                        },
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": {
                                "success": False,
                                "message": "Token validation failed",
                                "data": {
                                    "valid": False,
                                    "error": "Invalid or expired token"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
async def validate_patient_token(token_data: TokenValidationSchema):
    """
    Validate a patient JWT token.
    
    This endpoint can be used by client applications to verify if a token is still valid.
    It checks both the token signature and expiry, as well as whether the patient account
    is still active in the database.
    
    **Use Cases:**
    - Client-side token validation before making API calls
    - Token refresh decision logic
    - Security auditing and monitoring
    
    **Validation Checks:**
    1. JWT signature verification
    2. Token expiry check
    3. Patient account existence
    4. Patient account active status
    """
    try:
        validation_result = await patient_auth_service.validate_token(token_data.token)
        
        if validation_result.get("valid", False):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Token is valid",
                    "data": validation_result
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,  # Still 200, but with valid: false
                content={
                    "success": False,
                    "message": "Token validation failed",
                    "data": validation_result
                }
            )
            
    except Exception as e:
        logger.error(f"Error validating patient token: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Token validation failed due to server error",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )

@router.get(
    "/profile",
    response_model=PatientResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Patient profile retrieved successfully",
            "model": PatientResponseSchema
        },
        401: {
            "description": "Unauthorized - Invalid or missing token",
            "model": LoginErrorResponseSchema
        }
    }
)
async def get_patient_profile(current_patient: Dict[str, Any] = Depends(get_current_patient)):
    """
    Get current patient profile information.
    
    This endpoint returns the complete profile of the currently authenticated patient.
    Requires a valid JWT token in the Authorization header.
    
    **Authentication Required:**
    - Valid patient JWT token in Authorization header
    - Format: `Authorization: Bearer <token>`
    
    **Returned Information:**
    - Personal details (name, email, phone, date of birth)
    - Address information
    - Emergency contact details (if provided)
    - Medical history (if provided)
    - Insurance information (if provided)
    - Account verification status
    - Account creation and update timestamps
    
    **Security Notes:**
    - Sensitive information (password hash) is never returned
    - Only the authenticated patient can access their own profile
    """
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Profile retrieved successfully",
                "data": current_patient
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving patient profile: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Failed to retrieve profile",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )

@router.get(
    "/verification-status",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Verification status retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Verification status retrieved",
                        "data": {
                            "email_verified": True,
                            "phone_verified": False
                        }
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing token",
            "model": LoginErrorResponseSchema
        }
    }
)
async def get_verification_status(current_patient: Dict[str, Any] = Depends(get_current_patient)):
    """
    Get current patient's verification status.
    
    This endpoint returns the email and phone verification status for the 
    currently authenticated patient.
    
    **Authentication Required:**
    - Valid patient JWT token in Authorization header
    
    **Use Cases:**
    - Displaying verification status in user interface
    - Conditional feature access based on verification level
    - Prompting users to complete verification
    """
    try:
        patient_id = current_patient.get("patient_id")
        verification_status = await patient_auth_service.check_patient_verification_status(patient_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Verification status retrieved",
                "data": verification_status
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving verification status: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Failed to retrieve verification status",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        ) 