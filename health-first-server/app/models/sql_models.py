import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum, create_engine, Date, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy import Index
import enum
from app.schemas.provider import VerificationStatus

class AvailabilityStatus(enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    MAINTENANCE = "maintenance"

class RecurrencePattern(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class AppointmentType(enum.Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    TELEMEDICINE = "telemedicine"

class LocationType(enum.Enum):
    CLINIC = "clinic"
    HOSPITAL = "hospital"
    TELEMEDICINE = "telemedicine"
    HOME_VISIT = "home_visit"

class SlotStatus(enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"

class Base(DeclarativeBase):
    pass

class Provider(Base):
    __tablename__ = "providers"
    
    # Primary key - String for universal compatibility
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # Personal information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Professional information
    specialization = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False, index=True)
    years_of_experience = Column(Integer, nullable=False)
    
    # Clinic address (stored as separate fields)
    clinic_street = Column(String(200), nullable=False)
    clinic_city = Column(String(100), nullable=False)
    clinic_state = Column(String(50), nullable=False)
    clinic_zip = Column(String(20), nullable=False)
    
    # Status fields
    verification_status = Column(
        Enum(VerificationStatus, name="verification_status_enum"),
        default=VerificationStatus.PENDING,
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Additional indexes for performance
    __table_args__ = (
        Index('idx_provider_verification_status', 'verification_status'),
        Index('idx_provider_specialization', 'specialization'),
        Index('idx_provider_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'provider_id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'specialization': self.specialization,
            'license_number': self.license_number,
            'years_of_experience': self.years_of_experience,
            'clinic_address': {
                'street': self.clinic_street,
                'city': self.clinic_city,
                'state': self.clinic_state,
                'zip': self.clinic_zip
            },
            'verification_status': self.verification_status.value,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def __repr__(self):
        return f"<Provider {self.email}>"

class Patient(Base):
    __tablename__ = "patients"
    
    # Primary key - String for universal compatibility
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # Personal information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)
    
    # Address (stored as separate fields)
    address_street = Column(String(200), nullable=False)
    address_city = Column(String(100), nullable=False)
    address_state = Column(String(50), nullable=False)
    address_zip = Column(String(20), nullable=False)
    
    # Emergency contact (stored as JSON for flexibility)
    emergency_contact = Column(JSON, nullable=True)
    
    # Medical history (stored as JSON array)
    medical_history = Column(JSON, nullable=True)
    
    # Insurance information (stored as JSON)
    insurance_info = Column(JSON, nullable=True)
    
    # Verification status
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Additional indexes for performance
    __table_args__ = (
        Index('idx_patient_email_verified', 'email_verified'),
        Index('idx_patient_phone_verified', 'phone_verified'),
        Index('idx_patient_gender', 'gender'),
        Index('idx_patient_created_at', 'created_at'),
        Index('idx_patient_date_of_birth', 'date_of_birth'),
    )
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'patient_id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'address': {
                'street': self.address_street,
                'city': self.address_city,
                'state': self.address_state,
                'zip': self.address_zip
            },
            'emergency_contact': self.emergency_contact,
            'medical_history': self.medical_history or [],
            'insurance_info': self.insurance_info,
            'email_verified': self.email_verified,
            'phone_verified': self.phone_verified,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def __repr__(self):
        return f"<Patient {self.email}>"

class ProviderAvailability(Base):
    __tablename__ = "provider_availability"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # Foreign key to provider
    provider_id = Column(String(36), ForeignKey('providers.id'), nullable=False, index=True)
    
    # Time information
    date = Column(DateTime, nullable=False)  # Date for availability (YYYY-MM-DD)
    start_time = Column(String(5), nullable=False)  # HH:mm format (24-hour)
    end_time = Column(String(5), nullable=False)    # HH:mm format (24-hour)
    timezone = Column(String(50), nullable=False)   # e.g., "America/New_York"
    
    # Recurrence settings
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_pattern = Column(Enum(RecurrencePattern), nullable=True)
    recurrence_end_date = Column(DateTime, nullable=True)
    
    # Slot configuration
    slot_duration = Column(Integer, default=30, nullable=False)      # minutes
    break_duration = Column(Integer, default=0, nullable=False)      # minutes
    max_appointments_per_slot = Column(Integer, default=1, nullable=False)
    current_appointments = Column(Integer, default=0, nullable=False)
    
    # Appointment settings
    appointment_type = Column(Enum(AppointmentType), default=AppointmentType.CONSULTATION, nullable=False)
    status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.AVAILABLE, nullable=False)
    
    # Location information (stored as JSON)
    location = Column(JSON, nullable=False)  # {type, address, room_number}
    
    # Pricing information (stored as JSON)
    pricing = Column(JSON, nullable=True)  # {base_fee, insurance_accepted, currency}
    
    # Additional information
    notes = Column(Text(500), nullable=True)
    special_requirements = Column(JSON, nullable=True)  # Array of strings
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    provider = relationship("Provider")
    
    # Indexes
    __table_args__ = (
        Index('idx_availability_provider_date', 'provider_id', 'date'),
        Index('idx_availability_status', 'status'),
        Index('idx_availability_type', 'appointment_type'),
        Index('idx_availability_recurring', 'is_recurring'),
        Index('idx_availability_created_at', 'created_at'),
    )

class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # Foreign keys
    availability_id = Column(String(36), ForeignKey('provider_availability.id'), nullable=False, index=True)
    provider_id = Column(String(36), ForeignKey('providers.id'), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=True, index=True)
    
    # Time information
    slot_start_time = Column(DateTime, nullable=False)  # datetime with timezone
    slot_end_time = Column(DateTime, nullable=False)    # datetime with timezone
    
    # Booking information
    status = Column(Enum(SlotStatus), default=SlotStatus.AVAILABLE, nullable=False)
    appointment_type = Column(String(50), nullable=False)
    booking_reference = Column(String(100), unique=True, nullable=True, index=True)
    
    # Patient notes and requirements
    patient_notes = Column(Text(1000), nullable=True)
    special_instructions = Column(Text(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    booked_at = Column(DateTime, nullable=True)
    
    # Relationships
    availability = relationship("ProviderAvailability")
    provider = relationship("Provider")
    patient = relationship("Patient")
    
    # Indexes
    __table_args__ = (
        Index('idx_slot_provider_time', 'provider_id', 'slot_start_time'),
        Index('idx_slot_patient', 'patient_id'),
        Index('idx_slot_status', 'status'),
        Index('idx_slot_booking_ref', 'booking_reference'),
        Index('idx_slot_date_range', 'slot_start_time', 'slot_end_time'),
    ) 