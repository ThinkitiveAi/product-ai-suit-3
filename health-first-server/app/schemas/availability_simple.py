from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RecurrencePattern(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"  
    MONTHLY = "monthly"

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    TELEMEDICINE = "telemedicine"

class LocationType(str, Enum):
    CLINIC = "clinic"
    HOSPITAL = "hospital"
    TELEMEDICINE = "telemedicine"
    HOME_VISIT = "home_visit"

class SimpleLocationSchema(BaseModel):
    type: LocationType
    address: Optional[str] = None
    room_number: Optional[str] = None

class SimplePricingSchema(BaseModel):
    base_fee: Optional[float] = None
    insurance_accepted: bool = True
    currency: str = "USD"

class CreateAvailabilitySchema(BaseModel):
    date: date
    start_time: str = Field(..., description="Start time in HH:mm format")
    end_time: str = Field(..., description="End time in HH:mm format")
    timezone: str = "America/New_York"
    slot_duration: int = 30
    break_duration: int = 0
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[date] = None
    appointment_type: str = "consultation"
    max_appointments_per_slot: int = 1
    location: SimpleLocationSchema
    pricing: Optional[SimplePricingSchema] = None
    notes: Optional[str] = None
    special_requirements: List[str] = []

class AvailabilityResponseSchema(BaseModel):
    availability_id: str
    provider_id: str
    date: date
    start_time: str
    end_time: str
    timezone: str
    slot_duration: int
    break_duration: int
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[date] = None
    appointment_type: str
    max_appointments_per_slot: int
    current_appointments: int
    status: str
    location: SimpleLocationSchema
    pricing: Optional[SimplePricingSchema] = None
    notes: Optional[str] = None
    special_requirements: List[str]
    created_at: datetime
    updated_at: datetime

class AvailabilityListResponseSchema(BaseModel):
    success: bool = True
    message: str
    data: List[AvailabilityResponseSchema]
    total_count: int 