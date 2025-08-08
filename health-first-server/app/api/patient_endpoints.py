from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

from app.schemas.patient import (
    PatientRegistrationSchema,
    PatientRegistrationResponseSchema,
    ErrorResponseSchema,
    ValidationErrorResponseSchema,
    PatientUpdateSchema
)
from app.services.patient_service import PatientService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/patient", tags=["Patient Registration"])

# Initialize service
patient_service = PatientService()

@router.post(
    "/register",
    response_model=PatientRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Patient registered successfully",
            "model": PatientRegistrationResponseSchema
        },
        400: {
            "description": "Bad request - Invalid input data",
            "model": ErrorResponseSchema
        },
        409: {
            "description": "Conflict - Duplicate email or phone",
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
async def register_patient(registration_data: PatientRegistrationSchema):
    """
    Register a new patient with comprehensive validation and HIPAA compliance.
    
    This endpoint handles the complete patient registration process including:
    - Field validation (email format, phone format, password strength, date of birth, etc.)
    - Age verification for COPPA compliance (minimum 13 years old)
    - Uniqueness validation (email, phone number)
    - Secure password hashing with bcrypt
    - Medical data handling with HIPAA considerations
    - Database storage with proper indexing
    - Verification status initialization
    
    **Security Features:**
    - Passwords are hashed using bcrypt with 12+ salt rounds
    - Input sanitization to prevent injection attacks
    - No password logging or exposure in responses
    - Medical data encrypted at rest (when properly configured)
    - PHI access logging for HIPAA compliance (planned)
    
    **Validation Rules:**
    - Email: Must be valid format and unique
    - Phone: Must be international E.164 format and unique
    - Password: Minimum 8 characters with uppercase, lowercase, digit, and special character
    - Date of Birth: Must be valid date in past, minimum age 13 for COPPA compliance
    - Names: 2-50 characters, letters only with basic punctuation
    - Gender: Must be from allowed enum values
    - Address: Comprehensive validation with postal code format
    
    **HIPAA Compliance:**
    - Medical history and insurance information are optional
    - All medical data is sanitized and validated
    - Access logging planned for audit trails
    - Secure storage with encryption considerations
    
    **Response:**
    - Success (201): Returns patient ID, email, phone, and verification status
    - Validation Error (422): Returns field-specific validation errors
    - Conflict (409): Returns specific duplicate field errors
    - Server Error (500): Returns generic error message
    """
    try:
        # Register patient through service layer
        success, response_data = await patient_service.register_patient(registration_data)
        
        if success:
            # Successful registration
            logger.info(f"Patient registration successful: {response_data['data']['email']}")
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response_data
            )
        else:
            # Registration failed - determine appropriate status code
            if "duplicate" in response_data.get("message", "").lower() or \
               "already registered" in response_data.get("message", "").lower():
                # Duplicate data conflict
                logger.warning(f"Patient registration conflict: {response_data['message']}")
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content=response_data
                )
            else:
                # Other business logic errors
                logger.warning(f"Patient registration failed: {response_data['message']}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=response_data
                )
                
    except ValidationError as e:
        # Handle Pydantic validation errors
        logger.warning(f"Patient registration validation error: {str(e)}")
        
        # Extract field-specific errors
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
        # Handle unexpected errors
        logger.error(f"Unexpected error during patient registration: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Registration failed due to server error. Please try again later.",
                "error_code": "INTERNAL_ERROR"
            }
        )

@router.get(
    "/validate",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Validation result",
            "content": {
                "application/json": {
                    "examples": {
                        "valid": {
                            "summary": "Valid fields",
                            "value": {
                                "is_valid": True,
                                "errors": {}
                            }
                        },
                        "invalid": {
                            "summary": "Invalid fields",
                            "value": {
                                "is_valid": False,
                                "errors": {
                                    "email": ["This email address is already registered"]
                                }
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponseSchema
        }
    }
)
async def validate_patient_fields(
    email: Optional[str] = Query(None, description="Email to validate"),
    phone_number: Optional[str] = Query(None, description="Phone number to validate")
):
    """
    Validate patient field uniqueness before registration.
    
    This endpoint allows frontend applications to validate field uniqueness
    in real-time before submitting the full registration form.
    
    **Features:**
    - Real-time validation of email and phone uniqueness
    - Optimized for form field validation
    - No sensitive data exposure
    - Fast response for better UX
    
    **Use Cases:**
    - Form field validation during user input
    - Pre-registration validation
    - Duplicate check before submission
    
    **Privacy:**
    - Only checks uniqueness, doesn't expose existing data
    - No PHI (Protected Health Information) returned
    - Minimal logging for privacy protection
    """
    try:
        if not email and not phone_number:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "At least one field (email or phone_number) must be provided for validation"
                }
            )
        
        # Validate through service layer
        validation_result = await patient_service.validate_unique_fields(
            email=email,
            phone_number=phone_number
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=validation_result
        )
        
    except Exception as e:
        logger.error(f"Error during patient field validation: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Validation service temporarily unavailable",
                "error_code": "VALIDATION_ERROR"
            }
        )

@router.get(
    "/{patient_id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Patient information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Patient information retrieved successfully",
                        "data": {
                            "patient_id": "123e4567-e89b-12d3-a456-426614174000",
                            "first_name": "Jane",
                            "last_name": "Smith",
                            "email": "jane.smith@email.com",
                            "phone_number": "+1234567890",
                            "date_of_birth": "1990-05-15",
                            "gender": "female",
                            "address": {
                                "street": "456 Main Street",
                                "city": "Boston",
                                "state": "MA",
                                "zip": "02101"
                            },
                            "email_verified": False,
                            "phone_verified": False,
                            "is_active": True
                        }
                    }
                }
            }
        },
        404: {
            "description": "Patient not found",
            "model": ErrorResponseSchema
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponseSchema
        }
    }
)
async def get_patient_info(patient_id: str):
    """
    Get patient information by ID.
    
    This endpoint retrieves comprehensive patient information excluding sensitive data.
    
    **Features:**
    - Complete patient profile information
    - Sensitive data automatically filtered
    - HIPAA compliant data handling
    - Proper error handling for not found cases
    
    **Security:**
    - Password hash never returned
    - Access logging for audit trail (planned)
    - Rate limiting recommended for production
    
    **Data Returned:**
    - Basic demographics (name, email, phone, DOB, gender)
    - Address information
    - Verification status
    - Emergency contact (if provided)
    - Insurance information (if provided)
    - Medical history (if provided and authorized)
    
    **Note:**
    - This endpoint should be protected with authentication in production
    - Consider implementing role-based access control
    - PHI access should be logged for HIPAA compliance
    """
    try:
        # Get patient information through service layer
        patient_data = await patient_service.get_patient_by_id(patient_id)
        
        if patient_data:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Patient information retrieved successfully",
                    "data": patient_data
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "Patient not found",
                    "error_code": "PATIENT_NOT_FOUND"
                }
            )
            
    except Exception as e:
        logger.error(f"Error retrieving patient {patient_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Failed to retrieve patient information",
                "error_code": "RETRIEVAL_ERROR"
            }
        )

@router.put(
    "/{patient_id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Patient information updated successfully"
        },
        400: {
            "description": "Bad request - Invalid input data",
            "model": ErrorResponseSchema
        },
        404: {
            "description": "Patient not found",
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
async def update_patient_info(patient_id: str, update_data: PatientUpdateSchema):
    """
    Update patient information (excluding sensitive fields).
    
    This endpoint allows updating non-sensitive patient information while maintaining
    data integrity and HIPAA compliance.
    
    **Updatable Fields:**
    - Name (first_name, last_name)
    - Phone number
    - Address information
    - Emergency contact
    - Medical history
    - Insurance information
    
    **Security:**
    - Password and email cannot be updated through this endpoint
    - All updates are validated and sanitized
    - Timestamp automatically updated
    - Access logged for audit trail (planned)
    
    **Validation:**
    - Same validation rules as registration
    - Phone number uniqueness checked if updated
    - Medical history sanitized for security
    - Address format validated
    
    **HIPAA Compliance:**
    - Medical data updates logged
    - Sensitive information protected
    - Audit trail maintained
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        update_dict = update_data.model_dump(exclude_none=True)
        
        if not update_dict:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "No valid fields provided for update"
                }
            )
        
        # Update patient through service layer
        success, response_data = await patient_service.update_patient_info(patient_id, update_dict)
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data
            )
        else:
            status_code = status.HTTP_404_NOT_FOUND if "not found" in response_data.get("message", "").lower() \
                         else status.HTTP_400_BAD_REQUEST
            
            return JSONResponse(
                status_code=status_code,
                content=response_data
            )
            
    except ValidationError as e:
        # Handle Pydantic validation errors
        logger.warning(f"Patient update validation error: {str(e)}")
        
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
        logger.error(f"Unexpected error updating patient {patient_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Update failed due to server error",
                "error_code": "UPDATE_ERROR"
            }
        ) 