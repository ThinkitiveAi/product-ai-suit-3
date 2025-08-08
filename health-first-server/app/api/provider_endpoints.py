from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

from app.schemas.provider import (
    ProviderRegistrationSchema,
    ProviderRegistrationResponseSchema,
    ErrorResponseSchema,
    ValidationErrorResponseSchema
)
from app.services.provider_service import ProviderService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/provider", tags=["Provider Registration"])

# Initialize service
provider_service = ProviderService()

@router.post(
    "/register",
    response_model=ProviderRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Provider registered successfully",
            "model": ProviderRegistrationResponseSchema
        },
        400: {
            "description": "Bad request - Invalid input data",
            "model": ErrorResponseSchema
        },
        409: {
            "description": "Conflict - Duplicate email, phone, or license",
            "model": ErrorResponseSchema
        },
        422: {
            "description": "Validation error - Field validation failed",
            "model": ValidationErrorResponseSchema
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponseSchema
        }
    }
)
async def register_provider(registration_data: ProviderRegistrationSchema):
    """
    Register a new healthcare provider.
    
    This endpoint handles the complete provider registration process including:
    - Field validation (email format, phone format, password strength, etc.)
    - Uniqueness validation (email, phone number, license number)
    - Secure password hashing
    - Database storage
    - Verification status initialization
    
    **Security Features:**
    - Passwords are hashed using bcrypt with 12+ salt rounds
    - Input sanitization to prevent injection attacks
    - No password logging or exposure in responses
    
    **Validation Rules:**
    - Email: Must be valid format and unique
    - Phone: Must be international E.164 format and unique
    - Password: Minimum 8 characters with uppercase, lowercase, digit, and special character
    - License: Must be alphanumeric and unique
    - Names: 2-50 characters, letters only with basic punctuation
    - Experience: 0-50 years
    
    **Response:**
    - Success (201): Returns provider ID, email, and verification status
    - Validation Error (422): Returns field-specific validation errors
    - Conflict (409): Returns specific duplicate field errors
    - Server Error (500): Returns generic error message
    """
    try:
        # Register provider through service layer
        success, response_data = await provider_service.register_provider(registration_data)
        
        if success:
            # Successful registration
            logger.info(f"Provider registration successful: {response_data['data']['email']}")
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response_data
            )
        else:
            # Registration failed - determine appropriate status code
            if "duplicate" in response_data.get("message", "").lower() or \
               "already registered" in response_data.get("message", "").lower():
                # Duplicate data conflict
                logger.warning(f"Provider registration conflict: {response_data['message']}")
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content=response_data
                )
            elif "validation" in response_data.get("message", "").lower():
                # Validation error
                logger.warning(f"Provider registration validation error: {response_data['message']}")
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content=response_data
                )
            else:
                # Server error
                logger.error(f"Provider registration server error: {response_data['message']}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=response_data
                )
    
    except ValidationError as e:
        # Pydantic validation errors
        logger.warning(f"Pydantic validation error: {str(e)}")
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
        # Unexpected server errors
        logger.error(f"Unexpected error in provider registration: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "errors": {"server": ["Internal server error"]}
            }
        )

@router.get(
    "/validate",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Validation results",
            "content": {
                "application/json": {
                    "example": {
                        "is_valid": True,
                        "errors": {}
                    }
                }
            }
        }
    }
)
async def validate_unique_fields(
    email: Optional[str] = Query(None, description="Email address to validate"),
    phone_number: Optional[str] = Query(None, description="Phone number to validate"),
    license_number: Optional[str] = Query(None, description="License number to validate")
):
    """
    Validate that email, phone number, and license number are unique.
    
    This endpoint allows frontend applications to validate uniqueness
    before form submission to provide better user experience.
    
    **Parameters:**
    - email: Email address to check for uniqueness
    - phone_number: Phone number to check for uniqueness  
    - license_number: License number to check for uniqueness
    
    **Response:**
    - is_valid: Boolean indicating if all provided fields are unique
    - errors: Dictionary of field-specific error messages
    """
    try:
        validation_result = await provider_service.validate_unique_fields(
            email=email,
            phone_number=phone_number,
            license_number=license_number
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=validation_result
        )
    
    except Exception as e:
        logger.error(f"Error in field validation: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "is_valid": False,
                "errors": {"server": ["Unable to validate fields. Please try again."]}
            }
        )

@router.get(
    "/{provider_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Provider information retrieved successfully"
        },
        404: {
            "description": "Provider not found",
            "model": ErrorResponseSchema
        }
    }
)
async def get_provider(provider_id: str):
    """
    Get provider information by ID.
    
    **Note:** This endpoint excludes sensitive information like password hashes.
    
    **Parameters:**
    - provider_id: Unique provider identifier (UUID for SQL, ObjectId for MongoDB)
    
    **Response:**
    - Provider information excluding sensitive data
    """
    try:
        provider = await provider_service.get_provider_by_id(provider_id)
        
        if not provider:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "Provider not found",
                    "errors": {"provider_id": ["Provider with this ID does not exist"]}
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": provider
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting provider {provider_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Unable to retrieve provider information",
                "errors": {"server": ["Internal server error"]}
            }
        ) 