from datetime import date as Date, time as Time, datetime
from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
import pytz


# Enums for various choices
class RecurrencePattern(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    TELEMEDICINE = "telemedicine"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    MAINTENANCE = "maintenance"


class LocationType(str, Enum):
    CLINIC = "clinic"
    HOSPITAL = "hospital"
    TELEMEDICINE = "telemedicine"
    HOME_VISIT = "home_visit"


class SlotStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


# Simple schemas to avoid recursion issues
class SimpleLocationSchema(BaseModel):
    type: LocationType
    address: Optional[str] = None
    room_number: Optional[str] = None


class SimplePricingSchema(BaseModel):
    base_fee: Optional[float] = None
    insurance_accepted: bool = False
    currency: str = "USD"


# Main availability schemas
class CreateAvailabilitySchema(BaseModel):
    date: Date = Field(..., description="Date for availability (YYYY-MM-DD)")
    start_time: Time = Field(..., description="Start time (HH:MM)")
    end_time: Time = Field(..., description="End time (HH:MM)")
    timezone: str = Field(..., description="Timezone (e.g., 'America/New_York')")
    is_recurring: bool = Field(False, description="Whether this is a recurring availability")
    recurrence_pattern: Optional[RecurrencePattern] = Field(None, description="Pattern for recurring availability")
    recurrence_end_date: Optional[Date] = Field(None, description="End date for recurring availability")
    slot_duration: int = Field(30, description="Duration of each slot in minutes")
    break_duration: int = Field(0, description="Break duration between slots in minutes")
    max_appointments_per_slot: int = Field(1, description="Maximum appointments per slot")
    appointment_type: AppointmentType = Field(AppointmentType.CONSULTATION, description="Type of appointment")
    location: Optional[SimpleLocationSchema] = Field(None, description="Location details")
    pricing: Optional[SimplePricingSchema] = Field(None, description="Pricing information")
    notes: Optional[str] = Field(None, description="Additional notes")
    special_requirements: Optional[List[str]] = Field(None, description="Special requirements")

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        if v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v

    @model_validator(mode='after')
    def validate_times_and_recurrence(self):
        # Validate start_time < end_time
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        
        # Validate recurrence logic
        if self.is_recurring and not self.recurrence_pattern:
            raise ValueError("recurrence_pattern is required when is_recurring is True")
        
        if self.recurrence_pattern and not self.is_recurring:
            raise ValueError("is_recurring must be True when recurrence_pattern is set")
        
        if self.recurrence_end_date and not self.is_recurring:
            raise ValueError("recurrence_end_date can only be set for recurring availability")
        
        if self.recurrence_end_date and self.recurrence_end_date <= self.date:
            raise ValueError("recurrence_end_date must be after the start date")
        
        return self


class UpdateAvailabilitySchema(BaseModel):
    date: Optional[Date] = None
    start_time: Optional[Time] = None
    end_time: Optional[Time] = None
    timezone: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[Date] = None
    slot_duration: Optional[int] = None
    break_duration: Optional[int] = None
    status: Optional[AvailabilityStatus] = None
    max_appointments_per_slot: Optional[int] = None
    appointment_type: Optional[AppointmentType] = None
    location: Optional[SimpleLocationSchema] = None
    pricing: Optional[SimplePricingSchema] = None
    notes: Optional[str] = None
    special_requirements: Optional[List[str]] = None

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        if v and v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v


class AvailabilityResponseSchema(BaseModel):
    id: str
    provider_id: str
    date: Date
    start_time: Time
    end_time: Time
    timezone: str
    is_recurring: bool
    recurrence_pattern: Optional[RecurrencePattern]
    recurrence_end_date: Optional[Date]
    slot_duration: int
    break_duration: int
    status: AvailabilityStatus
    max_appointments_per_slot: int
    current_appointments: int
    appointment_type: AppointmentType
    location: Optional[SimpleLocationSchema]
    pricing: Optional[SimplePricingSchema]
    notes: Optional[str]
    special_requirements: Optional[List[str]]
    created_at: datetime
    updated_at: datetime


class AppointmentSlotSchema(BaseModel):
    id: str
    availability_id: str
    provider_id: str
    slot_start_time: datetime
    slot_end_time: datetime
    status: SlotStatus
    patient_id: Optional[str]
    appointment_type: str
    booking_reference: Optional[str]


class AvailabilityListResponseSchema(BaseModel):
    availabilities: List[AvailabilityResponseSchema]
    total: int
    page: int
    per_page: int


class AvailabilityCreateResponseSchema(BaseModel):
    availability: AvailabilityResponseSchema
    generated_slots: List[AppointmentSlotSchema]


class SlotListResponseSchema(BaseModel):
    slots: List[AppointmentSlotSchema]
    total: int
    page: int
    per_page: int


class ErrorResponseSchema(BaseModel):
    error: str
    message: str
    status_code: int


class ValidationErrorResponseSchema(BaseModel):
    error: str
    details: List[dict]
    status_code: int 