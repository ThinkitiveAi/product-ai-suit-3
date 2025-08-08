from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, date, timedelta, time
import logging
import secrets
import string
from dateutil.relativedelta import relativedelta
import pytz

from app.schemas.availability import (
    CreateAvailabilitySchema, 
    UpdateAvailabilitySchema,
    RecurrencePattern,
    AppointmentType,
    AvailabilityStatus,
    SlotStatus
)
from app.services.availability_repository import get_availability_repository
from app.services.provider_repository import get_provider_repository

logger = logging.getLogger(__name__)

class AvailabilityService:
    """
    Service class that handles provider availability management business logic.
    """
    
    def __init__(self):
        self.availability_repository = get_availability_repository()
        self.provider_repository = get_provider_repository()
    
    async def create_availability(self, provider_id: str, availability_data: CreateAvailabilitySchema) -> Tuple[bool, Dict[str, Any]]:
        """
        Create provider availability with automatic slot generation.
        
        Args:
            provider_id: Provider's unique identifier
            availability_data: Validated availability data
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Verify provider exists
            provider = await self.provider_repository.get_provider_by_id(provider_id)
            if not provider:
                return False, {
                    "error": "Provider not found",
                    "error_code": "PROVIDER_NOT_FOUND"
                }
            
            # Check for conflicting availability
            existing_availability = await self.availability_repository.get_provider_availability(
                provider_id, availability_data.date, availability_data.date
            )
            
            if existing_availability:
                # Check for time overlap
                for existing in existing_availability:
                    if self._check_time_overlap(
                        availability_data.start_time, availability_data.end_time,
                        existing["start_time"], existing["end_time"]
                    ):
                        return False, {
                            "error": "Time slot conflicts with existing availability",
                            "error_code": "TIME_CONFLICT",
                            "conflicting_availability_id": existing["availability_id"]
                        }
            
            # Prepare availability data for storage
            availability_dict = {
                "provider_id": provider_id,
                "date": availability_data.date,
                "start_time": availability_data.start_time,
                "end_time": availability_data.end_time,
                "timezone": availability_data.timezone,
                "is_recurring": availability_data.is_recurring,
                "recurrence_pattern": availability_data.recurrence_pattern.value if availability_data.recurrence_pattern else None,
                "recurrence_end_date": availability_data.recurrence_end_date,
                "slot_duration": availability_data.slot_duration,
                "break_duration": availability_data.break_duration,
                "max_appointments_per_slot": availability_data.max_appointments_per_slot,
                "current_appointments": 0,
                "appointment_type": availability_data.appointment_type.value,
                "status": AvailabilityStatus.AVAILABLE.value,
                "location": availability_data.location.model_dump(),
                "pricing": availability_data.pricing.model_dump() if availability_data.pricing else None,
                "notes": availability_data.notes,
                "special_requirements": availability_data.special_requirements or []
            }
            
            # Create availability record
            created_availability = await self.availability_repository.create_availability(availability_dict)
            
            # Generate appointment slots
            slots_created = await self._generate_appointment_slots(
                created_availability["availability_id"],
                provider_id,
                availability_data
            )
            
            # Handle recurring availability
            recurring_created = 0
            if availability_data.is_recurring and availability_data.recurrence_pattern:
                recurring_created = await self._create_recurring_availability(
                    provider_id,
                    availability_data
                )
            
            logger.info(f"Availability created successfully for provider {provider_id}: {created_availability['availability_id']}")
            
            return True, {
                "availability": created_availability,
                "slots_created": slots_created,
                "recurring_slots_created": recurring_created,
                "message": "Availability created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating availability for provider {provider_id}: {str(e)}")
            return False, {
                "error": "Failed to create availability",
                "error_code": "CREATION_ERROR",
                "details": str(e)
            }
    
    async def get_provider_availability(
        self, 
        provider_id: str, 
        start_date: date = None, 
        end_date: date = None,
        status_filter: AvailabilityStatus = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Get provider availability within date range.
        
        Args:
            provider_id: Provider's unique identifier
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            status_filter: Filter by availability status (optional)
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = date.today()
            if not end_date:
                end_date = start_date + timedelta(days=30)  # Default 30-day window
            
            availability_list = await self.availability_repository.get_provider_availability(
                provider_id, start_date, end_date
            )
            
            # Filter by status if provided
            if status_filter:
                availability_list = [
                    avail for avail in availability_list 
                    if avail["status"] == status_filter.value
                ]
            
            return True, {
                "availability": availability_list,
                "total_count": len(availability_list),
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting availability for provider {provider_id}: {str(e)}")
            return False, {
                "error": "Failed to get availability",
                "error_code": "RETRIEVAL_ERROR"
            }
    
    async def update_availability(
        self, 
        provider_id: str, 
        availability_id: str, 
        update_data: UpdateAvailabilitySchema
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Update provider availability.
        
        Args:
            provider_id: Provider's unique identifier
            availability_id: Availability record ID
            update_data: Update data
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Verify availability exists and belongs to provider
            existing_availability = await self.availability_repository.get_availability_by_id(availability_id)
            if not existing_availability:
                return False, {
                    "error": "Availability not found",
                    "error_code": "AVAILABILITY_NOT_FOUND"
                }
            
            if existing_availability["provider_id"] != provider_id:
                return False, {
                    "error": "Unauthorized to modify this availability",
                    "error_code": "UNAUTHORIZED"
                }
            
            # Prepare update dictionary
            update_dict = {}
            for field, value in update_data.model_dump(exclude_unset=True).items():
                if value is not None:
                    if field == "location" and value:
                        update_dict[field] = value
                    elif field == "pricing" and value:
                        update_dict[field] = value
                    elif hasattr(value, 'value'):  # Handle enum values
                        update_dict[field] = value.value
                    else:
                        update_dict[field] = value
            
            # Update availability
            updated_availability = await self.availability_repository.update_availability(
                availability_id, update_dict
            )
            
            if not updated_availability:
                return False, {
                    "error": "Failed to update availability",
                    "error_code": "UPDATE_FAILED"
                }
            
            # If time changes affect slots, regenerate them
            time_fields = ['start_time', 'end_time', 'slot_duration', 'break_duration']
            if any(field in update_dict for field in time_fields):
                # Delete existing slots
                existing_slots = await self.availability_repository.get_appointment_slots(availability_id)
                available_slots = [slot for slot in existing_slots if slot["status"] == "available"]
                
                if available_slots:
                    logger.info(f"Regenerating {len(available_slots)} slots due to time changes")
                    # Here you would implement slot regeneration logic
                    # For now, we'll just log the need for regeneration
            
            logger.info(f"Availability updated successfully: {availability_id}")
            
            return True, {
                "availability": updated_availability,
                "message": "Availability updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating availability {availability_id}: {str(e)}")
            return False, {
                "error": "Failed to update availability",
                "error_code": "UPDATE_ERROR"
            }
    
    async def delete_availability(self, provider_id: str, availability_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Delete provider availability and associated slots.
        
        Args:
            provider_id: Provider's unique identifier
            availability_id: Availability record ID
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Verify availability exists and belongs to provider
            existing_availability = await self.availability_repository.get_availability_by_id(availability_id)
            if not existing_availability:
                return False, {
                    "error": "Availability not found",
                    "error_code": "AVAILABILITY_NOT_FOUND"
                }
            
            if existing_availability["provider_id"] != provider_id:
                return False, {
                    "error": "Unauthorized to delete this availability",
                    "error_code": "UNAUTHORIZED"
                }
            
            # Check for booked appointments
            existing_slots = await self.availability_repository.get_appointment_slots(availability_id)
            booked_slots = [slot for slot in existing_slots if slot["status"] == "booked"]
            
            if booked_slots:
                return False, {
                    "error": "Cannot delete availability with booked appointments",
                    "error_code": "HAS_BOOKED_APPOINTMENTS",
                    "booked_slots_count": len(booked_slots)
                }
            
            # Delete availability (cascade will handle slots)
            success = await self.availability_repository.delete_availability(availability_id)
            
            if success:
                logger.info(f"Availability deleted successfully: {availability_id}")
                return True, {
                    "message": "Availability deleted successfully",
                    "deleted_slots_count": len(existing_slots)
                }
            else:
                return False, {
                    "error": "Failed to delete availability",
                    "error_code": "DELETION_FAILED"
                }
            
        except Exception as e:
            logger.error(f"Error deleting availability {availability_id}: {str(e)}")
            return False, {
                "error": "Failed to delete availability",
                "error_code": "DELETION_ERROR"
            }
    
    async def get_available_slots(
        self, 
        provider_id: str, 
        start_date: date = None, 
        end_date: date = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Get available appointment slots for a provider.
        
        Args:
            provider_id: Provider's unique identifier
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = date.today()
            if not end_date:
                end_date = start_date + timedelta(days=14)  # Default 2-week window
            
            available_slots = await self.availability_repository.get_available_slots(
                provider_id, start_date, end_date
            )
            
            return True, {
                "slots": available_slots,
                "total_count": len(available_slots),
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting available slots for provider {provider_id}: {str(e)}")
            return False, {
                "error": "Failed to get available slots",
                "error_code": "SLOTS_RETRIEVAL_ERROR"
            }
    
    async def _generate_appointment_slots(
        self, 
        availability_id: str, 
        provider_id: str, 
        availability_data: CreateAvailabilitySchema
    ) -> int:
        """
        Generate appointment slots from availability record.
        
        Args:
            availability_id: Parent availability ID
            provider_id: Provider ID
            availability_data: Availability configuration
            
        Returns:
            Number of slots created
        """
        try:
            # Parse time strings
            start_hour, start_min = map(int, availability_data.start_time.split(':'))
            end_hour, end_min = map(int, availability_data.end_time.split(':'))
            
            # Create timezone-aware datetime objects
            tz = pytz.timezone(availability_data.timezone)
            base_date = availability_data.date
            
            start_datetime = tz.localize(datetime.combine(base_date, time(start_hour, start_min)))
            end_datetime = tz.localize(datetime.combine(base_date, time(end_hour, end_min)))
            
            current_time = start_datetime
            slots_created = 0
            
            while current_time + timedelta(minutes=availability_data.slot_duration) <= end_datetime:
                slot_end_time = current_time + timedelta(minutes=availability_data.slot_duration)
                
                # Create slot
                slot_data = {
                    "availability_id": availability_id,
                    "provider_id": provider_id,
                    "slot_start_time": current_time.astimezone(pytz.UTC),
                    "slot_end_time": slot_end_time.astimezone(pytz.UTC),
                    "appointment_type": availability_data.appointment_type.value,
                    "status": SlotStatus.AVAILABLE.value
                }
                
                await self.availability_repository.create_appointment_slot(slot_data)
                slots_created += 1
                
                # Move to next slot (including break time)
                current_time = slot_end_time + timedelta(minutes=availability_data.break_duration)
            
            logger.info(f"Generated {slots_created} appointment slots for availability {availability_id}")
            return slots_created
            
        except Exception as e:
            logger.error(f"Error generating slots for availability {availability_id}: {str(e)}")
            return 0
    
    async def _create_recurring_availability(
        self, 
        provider_id: str, 
        availability_data: CreateAvailabilitySchema
    ) -> int:
        """
        Create recurring availability instances.
        
        Args:
            provider_id: Provider ID
            availability_data: Original availability data
            
        Returns:
            Number of recurring instances created
        """
        try:
            if not availability_data.is_recurring or not availability_data.recurrence_pattern:
                return 0
            
            current_date = availability_data.date
            end_date = availability_data.recurrence_end_date or (availability_data.date + timedelta(days=365))
            instances_created = 0
            
            while current_date < end_date:
                # Calculate next occurrence
                if availability_data.recurrence_pattern == RecurrencePattern.DAILY:
                    current_date += timedelta(days=1)
                elif availability_data.recurrence_pattern == RecurrencePattern.WEEKLY:
                    current_date += timedelta(weeks=1)
                elif availability_data.recurrence_pattern == RecurrencePattern.MONTHLY:
                    current_date += relativedelta(months=1)
                
                if current_date >= end_date:
                    break
                
                # Create new availability instance
                recurring_data = availability_data.model_copy()
                recurring_data.date = current_date
                recurring_data.is_recurring = False  # Avoid infinite recursion
                
                success, _ = await self.create_availability(provider_id, recurring_data)
                if success:
                    instances_created += 1
            
            logger.info(f"Created {instances_created} recurring availability instances")
            return instances_created
            
        except Exception as e:
            logger.error(f"Error creating recurring availability: {str(e)}")
            return 0
    
    def _check_time_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """
        Check if two time ranges overlap.
        
        Args:
            start1, end1: First time range
            start2, end2: Second time range
            
        Returns:
            True if times overlap
        """
        # Convert time strings to minutes for comparison
        def time_to_minutes(time_str: str) -> int:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        
        start1_min = time_to_minutes(start1)
        end1_min = time_to_minutes(end1)
        start2_min = time_to_minutes(start2)
        end2_min = time_to_minutes(end2)
        
        # Check for overlap
        return start1_min < end2_min and start2_min < end1_min
    
    def _generate_booking_reference(self) -> str:
        """Generate a unique booking reference."""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)) 