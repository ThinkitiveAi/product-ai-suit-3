from typing import Dict, Any, Optional
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

from app.schemas.availability import (
    CreateAvailabilitySchema,
    UpdateAvailabilitySchema,
    AvailabilityResponseSchema,
    AvailabilityCreateResponseSchema,
    AvailabilityListResponseSchema,
    SlotListResponseSchema,
    ErrorResponseSchema,
    ValidationErrorResponseSchema,
    AvailabilityStatus
)
from app.services.availability_service import AvailabilityService
from app.middleware.auth_middleware import get_current_provider, require_verified_and_active_provider

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/provider", tags=["Provider Availability Management"])

# Initialize service
availability_service = AvailabilityService()

@router.post(
    "/{provider_id}/availability",
    response_model=AvailabilityCreateResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_verified_and_active_provider)],
    responses={
        201: {
            "description": "Availability created successfully",
            "model": AvailabilityCreateResponseSchema
        },
        400: {
            "description": "Bad request - Invalid input data",
            "model": ErrorResponseSchema
        },
        401: {
            "description": "Unauthorized - Invalid or missing token",
            "model": ErrorResponseSchema
        },
        403: {
            "description": "Forbidden - Provider not verified or active",
            "model": ErrorResponseSchema
        },
        404: {
            "description": "Provider not found",
            "model": ErrorResponseSchema
        },
        409: {
            "description": "Conflict - Time slot already exists",
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
async def create_availability(
    provider_id: str,
    availability_data: CreateAvailabilitySchema,
    current_provider: Dict[str, Any] = Depends(get_current_provider)
):
    """
    Create provider availability with automatic appointment slot generation.
    
    This endpoint allows healthcare providers to set their available time slots for appointments.
    The system automatically generates individual appointment slots based on the availability configuration.
    
    **Key Features:**
    - Automatic slot generation based on duration and break settings
    - Support for recurring availability (daily, weekly, monthly)
    - Timezone-aware scheduling
    - Conflict detection with existing availability
    - Location and pricing configuration
    - Special requirements specification
    
    **Slot Generation:**
    - Slots are created based on `slot_duration` and `break_duration`
    - Each slot can accommodate up to `max_appointments_per_slot` appointments
    - Slots are automatically marked as available upon creation
    
    **Recurring Availability:**
    - Set `is_recurring` to true to create repeating availability
    - Specify `recurrence_pattern` (daily/weekly/monthly)
    - Set `recurrence_end_date` to limit the recurrence period
    
    **Authentication:**
    - Requires valid JWT token
    - Provider must be verified and active
    - Can only create availability for own provider ID
    
    **Validation:**
    - Date cannot be in the past
    - End time must be after start time
    - Timezone must be valid
    - No overlapping time slots on the same date
    """
    try:
        # Verify provider can only create their own availability
        if current_provider["provider_id"] != provider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Can only create availability for your own provider account",
                    "error_code": "UNAUTHORIZED_PROVIDER"
                }
            )
        
        # Create availability through service layer
        success, response_data = await availability_service.create_availability(
            provider_id, availability_data
        )
        
        if success:
            logger.info(f"Availability created successfully for provider {provider_id}")
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "success": True,
                    "message": response_data["message"],
                    "data": response_data["availability"],
                    "slots_created": response_data["slots_created"]
                }
            )
        else:
            error_code = response_data.get("error_code", "CREATION_ERROR")
            
            if error_code == "PROVIDER_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code
                    }
                )
            elif error_code == "TIME_CONFLICT":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code,
                        "details": {
                            "conflicting_availability_id": response_data.get("conflicting_availability_id")
                        }
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code
                    }
                )
                
    except ValidationError as e:
        logger.warning(f"Validation error creating availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "message": "Validation failed",
                "errors": e.errors()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )

@router.get(
    "/{provider_id}/availability",
    response_model=AvailabilityListResponseSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_provider)],
    responses={
        200: {
            "description": "Availability list retrieved successfully",
            "model": AvailabilityListResponseSchema
        },
        401: {
            "description": "Unauthorized - Invalid or missing token",
            "model": ErrorResponseSchema
        },
        403: {
            "description": "Forbidden - Can only access own availability",
            "model": ErrorResponseSchema
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponseSchema
        }
    }
)
async def get_provider_availability(
    provider_id: str,
    start_date: Optional[date] = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    status_filter: Optional[AvailabilityStatus] = Query(None, description="Filter by availability status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Number of records per page"),
    current_provider: Dict[str, Any] = Depends(get_current_provider)
):
    """
    Get provider availability within a date range.
    
    This endpoint retrieves all availability records for a provider within the specified date range.
    If no date range is provided, it defaults to the next 30 days from today.
    
    **Features:**
    - Date range filtering with optional start and end dates
    - Status filtering (available, booked, cancelled, blocked, maintenance)
    - Pagination support for large result sets
    - Automatic date range defaulting
    
    **Default Behavior:**
    - If no start_date is provided, uses today's date
    - If no end_date is provided, uses 30 days from start_date
    - Results are ordered by date and start time
    
    **Access Control:**
    - Providers can only access their own availability
    - Requires valid authentication token
    
    **Response:**
    - List of availability records with complete details
    - Pagination metadata (total count, page info)
    - Date range used for filtering
    """
    try:
        # Verify provider can only access their own availability
        if current_provider["provider_id"] != provider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Can only access your own availability",
                    "error_code": "UNAUTHORIZED_PROVIDER"
                }
            )
        
        # Get availability through service layer
        success, response_data = await availability_service.get_provider_availability(
            provider_id, start_date, end_date, status_filter
        )
        
        if success:
            availability_list = response_data["availability"]
            total_count = response_data["total_count"]
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_list = availability_list[start_idx:end_idx]
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Availability retrieved successfully",
                    "data": paginated_list,
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "date_range": response_data["date_range"]
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": response_data["error"],
                    "error_code": response_data.get("error_code", "RETRIEVAL_ERROR")
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )

@router.put(
    "/{provider_id}/availability/{availability_id}",
    response_model=AvailabilityResponseSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_verified_and_active_provider)],
    responses={
        200: {
            "description": "Availability updated successfully",
            "model": AvailabilityResponseSchema
        },
        400: {
            "description": "Bad request - Invalid input data",
            "model": ErrorResponseSchema
        },
        401: {
            "description": "Unauthorized - Invalid or missing token",
            "model": ErrorResponseSchema
        },
        403: {
            "description": "Forbidden - Provider not verified, active, or unauthorized",
            "model": ErrorResponseSchema
        },
        404: {
            "description": "Availability not found",
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
async def update_availability(
    provider_id: str,
    availability_id: str,
    update_data: UpdateAvailabilitySchema,
    current_provider: Dict[str, Any] = Depends(get_current_provider)
):
    """
    Update provider availability.
    
    This endpoint allows providers to modify their existing availability records.
    Updates can include time changes, status modifications, location updates, and more.
    
    **Updatable Fields:**
    - Time settings (start_time, end_time, slot_duration, break_duration)
    - Status (available, blocked, maintenance, cancelled)
    - Location information
    - Pricing information
    - Notes and special requirements
    - Appointment type and capacity settings
    
    **Important Notes:**
    - Time changes may affect existing appointment slots
    - Cannot modify availability with booked appointments to certain statuses
    - All time fields use 24-hour format (HH:mm)
    - Timezone changes require careful consideration of existing slots
    
    **Access Control:**
    - Providers can only update their own availability
    - Requires provider to be verified and active
    - Availability must belong to the authenticated provider
    
    **Validation:**
    - All standard validation rules apply
    - End time must be after start time if both are updated
    - Valid timezone if timezone is being updated
    """
    try:
        # Verify provider can only update their own availability
        if current_provider["provider_id"] != provider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Can only update your own availability",
                    "error_code": "UNAUTHORIZED_PROVIDER"
                }
            )
        
        # Update availability through service layer
        success, response_data = await availability_service.update_availability(
            provider_id, availability_id, update_data
        )
        
        if success:
            logger.info(f"Availability updated successfully: {availability_id}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": response_data["message"],
                    "data": response_data["availability"]
                }
            )
        else:
            error_code = response_data.get("error_code", "UPDATE_ERROR")
            
            if error_code == "AVAILABILITY_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code
                    }
                )
            elif error_code == "UNAUTHORIZED":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code
                    }
                )
                
    except ValidationError as e:
        logger.warning(f"Validation error updating availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "message": "Validation failed",
                "errors": e.errors()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )

@router.delete(
    "/{provider_id}/availability/{availability_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_verified_and_active_provider)],
    responses={
        200: {
            "description": "Availability deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Availability deleted successfully",
                        "deleted_slots_count": 12
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing token",
            "model": ErrorResponseSchema
        },
        403: {
            "description": "Forbidden - Provider not verified, active, or unauthorized",
            "model": ErrorResponseSchema
        },
        404: {
            "description": "Availability not found",
            "model": ErrorResponseSchema
        },
        409: {
            "description": "Conflict - Cannot delete availability with booked appointments",
            "model": ErrorResponseSchema
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponseSchema
        }
    }
)
async def delete_availability(
    provider_id: str,
    availability_id: str,
    current_provider: Dict[str, Any] = Depends(get_current_provider)
):
    """
    Delete provider availability and associated appointment slots.
    
    This endpoint permanently removes an availability record and all its associated appointment slots.
    This operation cannot be undone.
    
    **Important Restrictions:**
    - Cannot delete availability that has booked appointments
    - All associated available slots will be deleted
    - This action is permanent and cannot be reversed
    
    **Safety Checks:**
    - Verifies no appointments are booked before deletion
    - Returns error with booking count if deletion is blocked
    - Provides confirmation of number of slots deleted
    
    **Access Control:**
    - Providers can only delete their own availability
    - Requires provider to be verified and active
    - Availability must belong to the authenticated provider
    
    **Use Cases:**
    - Remove incorrectly created availability
    - Cancel availability periods due to schedule changes
    - Clean up unused availability records
    
    **Alternative Actions:**
    - To temporarily disable: Update status to 'blocked' or 'cancelled'
    - To modify: Use the update endpoint instead
    """
    try:
        # Verify provider can only delete their own availability
        if current_provider["provider_id"] != provider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Can only delete your own availability",
                    "error_code": "UNAUTHORIZED_PROVIDER"
                }
            )
        
        # Delete availability through service layer
        success, response_data = await availability_service.delete_availability(
            provider_id, availability_id
        )
        
        if success:
            logger.info(f"Availability deleted successfully: {availability_id}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": response_data["message"],
                    "deleted_slots_count": response_data["deleted_slots_count"]
                }
            )
        else:
            error_code = response_data.get("error_code", "DELETION_ERROR")
            
            if error_code == "AVAILABILITY_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code
                    }
                )
            elif error_code == "UNAUTHORIZED":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code
                    }
                )
            elif error_code == "HAS_BOOKED_APPOINTMENTS":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code,
                        "details": {
                            "booked_slots_count": response_data["booked_slots_count"]
                        }
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": response_data["error"],
                        "error_code": error_code
                    }
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )

@router.get(
    "/{provider_id}/slots",
    response_model=SlotListResponseSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_provider)],
    responses={
        200: {
            "description": "Available slots retrieved successfully",
            "model": SlotListResponseSchema
        },
        401: {
            "description": "Unauthorized - Invalid or missing token",
            "model": ErrorResponseSchema
        },
        403: {
            "description": "Forbidden - Can only access own slots",
            "model": ErrorResponseSchema
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponseSchema
        }
    }
)
async def get_available_slots(
    provider_id: str,
    start_date: Optional[date] = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    current_provider: Dict[str, Any] = Depends(get_current_provider)
):
    """
    Get available appointment slots for a provider.
    
    This endpoint retrieves all available (unboked) appointment slots for a provider
    within the specified date range. This is useful for displaying available appointment
    times to patients or for scheduling purposes.
    
    **Features:**
    - Returns only available (unbooked) slots
    - Date range filtering with intelligent defaults
    - Timezone-aware slot times
    - Detailed slot information including duration and type
    
    **Default Behavior:**
    - If no start_date is provided, uses today's date
    - If no end_date is provided, uses 2 weeks from start_date
    - Results are ordered by slot start time
    - Only returns slots with status 'available'
    
    **Slot Information:**
    - Each slot includes start/end times with timezone
    - Appointment type and duration
    - Associated availability record ID
    - Booking reference placeholder
    
    **Use Cases:**
    - Patient booking interfaces
    - Provider schedule overview
    - Appointment availability checking
    - Scheduling system integration
    
    **Access Control:**
    - Providers can only access their own available slots
    - Requires valid authentication token
    """
    try:
        # Verify provider can only access their own slots
        if current_provider["provider_id"] != provider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Can only access your own slots",
                    "error_code": "UNAUTHORIZED_PROVIDER"
                }
            )
        
        # Get available slots through service layer
        success, response_data = await availability_service.get_available_slots(
            provider_id, start_date, end_date
        )
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Available slots retrieved successfully",
                    "data": response_data["slots"],
                    "total_count": response_data["total_count"],
                    "date_range": response_data["date_range"]
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": response_data["error"],
                    "error_code": response_data.get("error_code", "SLOTS_RETRIEVAL_ERROR")
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting available slots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        ) 