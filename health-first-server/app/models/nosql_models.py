from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from app.schemas.provider import VerificationStatus

class ProviderDocument:
    """
    MongoDB document model for Provider collection.
    This class provides methods for document creation, validation, and conversion.
    """
    
    @staticmethod
    def create_document(
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        password_hash: str,
        specialization: str,
        license_number: str,
        years_of_experience: int,
        clinic_address: Dict[str, str],
        verification_status: VerificationStatus = VerificationStatus.PENDING,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """
        Create a MongoDB document for a provider.
        
        Args:
            All provider fields
            
        Returns:
            Dictionary representing the MongoDB document
        """
        now = datetime.utcnow()
        
        return {
            "_id": ObjectId(),
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_number": phone_number,
            "password_hash": password_hash,
            "specialization": specialization,
            "license_number": license_number,
            "years_of_experience": years_of_experience,
            "clinic_address": {
                "street": clinic_address["street"],
                "city": clinic_address["city"],
                "state": clinic_address["state"],
                "zip": clinic_address["zip"]
            },
            "verification_status": verification_status.value,
            "is_active": is_active,
            "created_at": now,
            "updated_at": now
        }
    
    @staticmethod
    def to_dict(document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MongoDB document to standardized dictionary format.
        
        Args:
            document: MongoDB document
            
        Returns:
            Standardized dictionary representation
        """
        if not document:
            return {}
        
        return {
            "provider_id": str(document["_id"]),
            "first_name": document["first_name"],
            "last_name": document["last_name"],
            "email": document["email"],
            "phone_number": document["phone_number"],
            "specialization": document["specialization"],
            "license_number": document["license_number"],
            "years_of_experience": document["years_of_experience"],
            "clinic_address": document["clinic_address"],
            "verification_status": document["verification_status"],
            "is_active": document["is_active"],
            "created_at": document["created_at"],
            "updated_at": document["updated_at"]
        }
    
    @staticmethod
    def get_collection_indexes() -> list:
        """
        Get the list of indexes that should be created for the providers collection.
        
        Returns:
            List of index specifications
        """
        return [
            # Unique indexes for business constraints
            {"key": [("email", 1)], "unique": True, "name": "idx_email_unique"},
            {"key": [("phone_number", 1)], "unique": True, "name": "idx_phone_unique"},
            {"key": [("license_number", 1)], "unique": True, "name": "idx_license_unique"},
            
            # Performance indexes
            {"key": [("verification_status", 1)], "name": "idx_verification_status"},
            {"key": [("specialization", 1)], "name": "idx_specialization"},
            {"key": [("created_at", 1)], "name": "idx_created_at"},
            {"key": [("is_active", 1)], "name": "idx_is_active"},
            
            # Compound indexes for common queries
            {"key": [("verification_status", 1), ("is_active", 1)], "name": "idx_status_active"},
            {"key": [("specialization", 1), ("verification_status", 1)], "name": "idx_spec_status"}
        ]
    
    @staticmethod
    def get_validation_schema() -> Dict[str, Any]:
        """
        Get MongoDB collection validation schema.
        
        Returns:
            JSON schema for document validation
        """
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "first_name", "last_name", "email", "phone_number", 
                    "password_hash", "specialization", "license_number", 
                    "years_of_experience", "clinic_address", "verification_status",
                    "is_active", "created_at", "updated_at"
                ],
                "properties": {
                    "first_name": {
                        "bsonType": "string",
                        "minLength": 2,
                        "maxLength": 50
                    },
                    "last_name": {
                        "bsonType": "string",
                        "minLength": 2,
                        "maxLength": 50
                    },
                    "email": {
                        "bsonType": "string",
                        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    },
                    "phone_number": {
                        "bsonType": "string",
                        "pattern": r"^\+[1-9]\d{1,14}$"
                    },
                    "password_hash": {
                        "bsonType": "string",
                        "minLength": 1
                    },
                    "specialization": {
                        "bsonType": "string",
                        "minLength": 3,
                        "maxLength": 100
                    },
                    "license_number": {
                        "bsonType": "string",
                        "minLength": 1,
                        "maxLength": 50
                    },
                    "years_of_experience": {
                        "bsonType": "int",
                        "minimum": 0,
                        "maximum": 50
                    },
                    "clinic_address": {
                        "bsonType": "object",
                        "required": ["street", "city", "state", "zip"],
                        "properties": {
                            "street": {"bsonType": "string", "maxLength": 200},
                            "city": {"bsonType": "string", "maxLength": 100},
                            "state": {"bsonType": "string", "maxLength": 50},
                            "zip": {"bsonType": "string", "maxLength": 20}
                        }
                    },
                    "verification_status": {
                        "bsonType": "string",
                        "enum": ["pending", "verified", "rejected"]
                    },
                    "is_active": {
                        "bsonType": "bool"
                    },
                    "created_at": {
                        "bsonType": "date"
                    },
                    "updated_at": {
                        "bsonType": "date"
                    }
                }
            }
        }

class PatientDocument:
    """
    MongoDB document model for Patient collection.
    This class provides methods for document creation, validation, and conversion.
    """
    
    @staticmethod
    def create_document(
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        password_hash: str,
        date_of_birth: str,
        gender: str,
        address: Dict[str, str],
        emergency_contact: Optional[Dict[str, str]] = None,
        medical_history: Optional[List[str]] = None,
        insurance_info: Optional[Dict[str, str]] = None,
        email_verified: bool = False,
        phone_verified: bool = False,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """
        Create a MongoDB document for a patient.
        
        Args:
            All patient fields
            
        Returns:
            Dictionary representing the MongoDB document
        """
        now = datetime.utcnow()
        
        return {
            "_id": ObjectId(),
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_number": phone_number,
            "password_hash": password_hash,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "address": {
                "street": address["street"],
                "city": address["city"],
                "state": address["state"],
                "zip": address["zip"]
            },
            "emergency_contact": emergency_contact,
            "medical_history": medical_history or [],
            "insurance_info": insurance_info,
            "email_verified": email_verified,
            "phone_verified": phone_verified,
            "is_active": is_active,
            "created_at": now,
            "updated_at": now
        }
    
    @staticmethod
    def to_dict(document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MongoDB document to standardized dictionary format.
        
        Args:
            document: MongoDB document
            
        Returns:
            Standardized dictionary representation
        """
        if not document:
            return {}
        
        return {
            "patient_id": str(document["_id"]),
            "first_name": document["first_name"],
            "last_name": document["last_name"],
            "email": document["email"],
            "phone_number": document["phone_number"],
            "date_of_birth": document["date_of_birth"],
            "gender": document["gender"],
            "address": document["address"],
            "emergency_contact": document.get("emergency_contact"),
            "medical_history": document.get("medical_history", []),
            "insurance_info": document.get("insurance_info"),
            "email_verified": document["email_verified"],
            "phone_verified": document["phone_verified"],
            "is_active": document["is_active"],
            "created_at": document["created_at"],
            "updated_at": document["updated_at"]
        }
    
    @staticmethod
    def get_collection_indexes() -> list:
        """
        Get the list of indexes that should be created for the patients collection.
        
        Returns:
            List of index specifications
        """
        return [
            # Unique indexes for business constraints
            {"key": [("email", 1)], "unique": True, "name": "idx_email_unique"},
            {"key": [("phone_number", 1)], "unique": True, "name": "idx_phone_unique"},
            
            # Performance indexes
            {"key": [("email_verified", 1)], "name": "idx_email_verified"},
            {"key": [("phone_verified", 1)], "name": "idx_phone_verified"},
            {"key": [("gender", 1)], "name": "idx_gender"},
            {"key": [("date_of_birth", 1)], "name": "idx_date_of_birth"},
            {"key": [("created_at", 1)], "name": "idx_created_at"},
            {"key": [("is_active", 1)], "name": "idx_is_active"},
            
            # Compound indexes for common queries
            {"key": [("email_verified", 1), ("phone_verified", 1)], "name": "idx_verification_status"},
            {"key": [("gender", 1), ("date_of_birth", 1)], "name": "idx_demographics"}
        ]
    
    @staticmethod
    def get_validation_schema() -> Dict[str, Any]:
        """
        Get MongoDB collection validation schema.
        
        Returns:
            JSON schema for document validation
        """
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "first_name", "last_name", "email", "phone_number", 
                    "password_hash", "date_of_birth", "gender", "address",
                    "email_verified", "phone_verified", "is_active", 
                    "created_at", "updated_at"
                ],
                "properties": {
                    "first_name": {
                        "bsonType": "string",
                        "minLength": 2,
                        "maxLength": 50
                    },
                    "last_name": {
                        "bsonType": "string",
                        "minLength": 2,
                        "maxLength": 50
                    },
                    "email": {
                        "bsonType": "string",
                        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    },
                    "phone_number": {
                        "bsonType": "string",
                        "pattern": r"^\+[1-9]\d{1,14}$"
                    },
                    "password_hash": {
                        "bsonType": "string",
                        "minLength": 1
                    },
                    "date_of_birth": {
                        "bsonType": "string"
                    },
                    "gender": {
                        "bsonType": "string",
                        "enum": ["male", "female", "other", "prefer_not_to_say"]
                    },
                    "address": {
                        "bsonType": "object",
                        "required": ["street", "city", "state", "zip"],
                        "properties": {
                            "street": {"bsonType": "string", "maxLength": 200},
                            "city": {"bsonType": "string", "maxLength": 100},
                            "state": {"bsonType": "string", "maxLength": 50},
                            "zip": {"bsonType": "string", "maxLength": 20}
                        }
                    },
                    "emergency_contact": {
                        "bsonType": ["object", "null"],
                        "properties": {
                            "name": {"bsonType": "string", "maxLength": 100},
                            "phone": {"bsonType": "string"},
                            "relationship": {"bsonType": "string", "maxLength": 50}
                        }
                    },
                    "medical_history": {
                        "bsonType": ["array", "null"],
                        "items": {"bsonType": "string"}
                    },
                    "insurance_info": {
                        "bsonType": ["object", "null"],
                        "properties": {
                            "provider": {"bsonType": "string"},
                            "policy_number": {"bsonType": "string"}
                        }
                    },
                    "email_verified": {
                        "bsonType": "bool"
                    },
                    "phone_verified": {
                        "bsonType": "bool"
                    },
                    "is_active": {
                        "bsonType": "bool"
                    },
                    "created_at": {
                        "bsonType": "date"
                    },
                    "updated_at": {
                        "bsonType": "date"
                    }
                }
            }
        }

class ProviderAvailabilityDocument:
    """
    MongoDB document model for Provider Availability collection.
    """
    
    @staticmethod
    def create_document(
        provider_id: str,
        date: datetime,
        start_time: str,
        end_time: str,
        timezone: str,
        slot_duration: int = 30,
        break_duration: int = 0,
        is_recurring: bool = False,
        recurrence_pattern: str = None,
        recurrence_end_date: datetime = None,
        max_appointments_per_slot: int = 1,
        current_appointments: int = 0,
        appointment_type: str = "consultation",
        status: str = "available",
        location: Dict[str, Any] = None,
        pricing: Dict[str, Any] = None,
        notes: str = None,
        special_requirements: List[str] = None
    ) -> Dict[str, Any]:
        """Create a MongoDB document for provider availability."""
        now = datetime.utcnow()
        
        return {
            "_id": ObjectId(),
            "provider_id": provider_id,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "timezone": timezone,
            "is_recurring": is_recurring,
            "recurrence_pattern": recurrence_pattern,
            "recurrence_end_date": recurrence_end_date,
            "slot_duration": slot_duration,
            "break_duration": break_duration,
            "max_appointments_per_slot": max_appointments_per_slot,
            "current_appointments": current_appointments,
            "appointment_type": appointment_type,
            "status": status,
            "location": location or {},
            "pricing": pricing,
            "notes": notes,
            "special_requirements": special_requirements or [],
            "created_at": now,
            "updated_at": now
        }
    
    @staticmethod
    def to_dict(document: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to standardized dictionary."""
        return {
            "availability_id": str(document["_id"]),
            "provider_id": document["provider_id"],
            "date": document["date"],
            "start_time": document["start_time"],
            "end_time": document["end_time"],
            "timezone": document["timezone"],
            "is_recurring": document["is_recurring"],
            "recurrence_pattern": document.get("recurrence_pattern"),
            "recurrence_end_date": document.get("recurrence_end_date"),
            "slot_duration": document["slot_duration"],
            "break_duration": document["break_duration"],
            "max_appointments_per_slot": document["max_appointments_per_slot"],
            "current_appointments": document["current_appointments"],
            "appointment_type": document["appointment_type"],
            "status": document["status"],
            "location": document["location"],
            "pricing": document.get("pricing"),
            "notes": document.get("notes"),
            "special_requirements": document["special_requirements"],
            "created_at": document["created_at"],
            "updated_at": document["updated_at"]
        }
    
    @staticmethod
    def get_collection_indexes() -> list:
        """Get indexes for provider availability collection."""
        return [
            {"key": [("provider_id", 1), ("date", 1)], "name": "idx_availability_provider_date"},
            {"key": [("provider_id", 1), ("status", 1)], "name": "idx_availability_provider_status"},
            {"key": [("date", 1), ("status", 1)], "name": "idx_availability_date_status"},
            {"key": [("appointment_type", 1)], "name": "idx_availability_type"},
            {"key": [("is_recurring", 1)], "name": "idx_availability_recurring"},
            {"key": [("created_at", 1)], "name": "idx_availability_created_at"}
        ]

class AppointmentSlotDocument:
    """
    MongoDB document model for Appointment Slots collection.
    """
    
    @staticmethod
    def create_document(
        availability_id: str,
        provider_id: str,
        slot_start_time: datetime,
        slot_end_time: datetime,
        appointment_type: str,
        status: str = "available",
        patient_id: str = None,
        booking_reference: str = None,
        patient_notes: str = None,
        special_instructions: str = None
    ) -> Dict[str, Any]:
        """Create a MongoDB document for appointment slot."""
        now = datetime.utcnow()
        
        return {
            "_id": ObjectId(),
            "availability_id": availability_id,
            "provider_id": provider_id,
            "patient_id": patient_id,
            "slot_start_time": slot_start_time,
            "slot_end_time": slot_end_time,
            "status": status,
            "appointment_type": appointment_type,
            "booking_reference": booking_reference,
            "patient_notes": patient_notes,
            "special_instructions": special_instructions,
            "created_at": now,
            "updated_at": now,
            "booked_at": now if status == "booked" else None
        }
    
    @staticmethod
    def to_dict(document: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to standardized dictionary."""
        return {
            "slot_id": str(document["_id"]),
            "availability_id": document["availability_id"],
            "provider_id": document["provider_id"],
            "patient_id": document.get("patient_id"),
            "slot_start_time": document["slot_start_time"],
            "slot_end_time": document["slot_end_time"],
            "status": document["status"],
            "appointment_type": document["appointment_type"],
            "booking_reference": document.get("booking_reference"),
            "patient_notes": document.get("patient_notes"),
            "special_instructions": document.get("special_instructions"),
            "created_at": document["created_at"],
            "updated_at": document["updated_at"],
            "booked_at": document.get("booked_at")
        }
    
    @staticmethod
    def get_collection_indexes() -> list:
        """Get indexes for appointment slots collection."""
        return [
            {"key": [("provider_id", 1), ("slot_start_time", 1)], "name": "idx_slot_provider_time"},
            {"key": [("availability_id", 1)], "name": "idx_slot_availability"},
            {"key": [("patient_id", 1)], "name": "idx_slot_patient"},
            {"key": [("status", 1)], "name": "idx_slot_status"},
            {"key": [("booking_reference", 1)], "unique": True, "sparse": True, "name": "idx_slot_booking_ref_unique"},
            {"key": [("slot_start_time", 1), ("slot_end_time", 1)], "name": "idx_slot_time_range"},
            {"key": [("created_at", 1)], "name": "idx_slot_created_at"}
        ] 