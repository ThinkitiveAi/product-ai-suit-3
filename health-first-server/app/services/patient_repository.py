from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pymongo.errors import DuplicateKeyError, PyMongoError
import logging

from app.config import config, DatabaseType
from app.database.connections import db_manager
from app.models.sql_models import Patient
from app.models.nosql_models import PatientDocument

logger = logging.getLogger(__name__)

class PatientRepositoryInterface(ABC):
    """Abstract interface for patient repository operations."""
    
    @abstractmethod
    async def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new patient."""
        pass
    
    @abstractmethod
    async def get_patient_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get patient by email."""
        pass
    
    @abstractmethod
    async def get_patient_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get patient by phone number."""
        pass
    
    @abstractmethod
    async def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by ID."""
        pass
    
    @abstractmethod
    async def update_patient(self, patient_id: str, update_data: Dict[str, Any]) -> bool:
        """Update patient information."""
        pass

class SQLPatientRepository(PatientRepositoryInterface):
    """SQL implementation of patient repository."""
    
    async def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new patient in SQL database.
        
        Args:
            patient_data: Patient information dictionary
            
        Returns:
            Created patient data
            
        Raises:
            ValueError: If duplicate email or phone exists
            RuntimeError: If database operation fails
        """
        try:
            with db_manager.get_sql_session() as session:
                # Create patient instance
                patient = Patient(
                    first_name=patient_data["first_name"],
                    last_name=patient_data["last_name"],
                    email=patient_data["email"],
                    phone_number=patient_data["phone_number"],
                    password_hash=patient_data["password_hash"],
                    date_of_birth=patient_data["date_of_birth"],
                    gender=patient_data["gender"],
                    address_street=patient_data["address"]["street"],
                    address_city=patient_data["address"]["city"],
                    address_state=patient_data["address"]["state"],
                    address_zip=patient_data["address"]["zip"],
                    emergency_contact=patient_data.get("emergency_contact"),
                    medical_history=patient_data.get("medical_history"),
                    insurance_info=patient_data.get("insurance_info"),
                    email_verified=False,
                    phone_verified=False,
                    is_active=True
                )
                
                session.add(patient)
                session.flush()  # Get the ID without committing
                
                result = patient.to_dict()
                session.commit()
                
                logger.info(f"Patient created successfully with ID: {result['patient_id']}")
                return result
                
        except IntegrityError as e:
            error_message = str(e.orig).lower()
            if "email" in error_message:
                raise ValueError("Email address is already registered")
            elif "phone" in error_message:
                raise ValueError("Phone number is already registered")
            else:
                raise ValueError("Duplicate entry detected")
        except SQLAlchemyError as e:
            logger.error(f"Database error creating patient: {str(e)}")
            raise RuntimeError("Failed to create patient due to database error")
    
    async def get_patient_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get patient by email from SQL database."""
        try:
            with db_manager.get_sql_session() as session:
                patient = session.query(Patient).filter(Patient.email == email).first()
                return patient.to_dict() if patient else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting patient by email: {str(e)}")
            return None
    
    async def get_patient_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get patient by phone number from SQL database."""
        try:
            with db_manager.get_sql_session() as session:
                patient = session.query(Patient).filter(Patient.phone_number == phone_number).first()
                return patient.to_dict() if patient else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting patient by phone: {str(e)}")
            return None
    
    async def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by ID from SQL database."""
        try:
            with db_manager.get_sql_session() as session:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                return patient.to_dict() if patient else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting patient by ID: {str(e)}")
            return None
    
    async def update_patient(self, patient_id: str, update_data: Dict[str, Any]) -> bool:
        """Update patient information in SQL database."""
        try:
            with db_manager.get_sql_session() as session:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                
                if not patient:
                    return False
                
                # Update fields that are provided
                for field, value in update_data.items():
                    if field == "address" and value:
                        patient.address_street = value["street"]
                        patient.address_city = value["city"]
                        patient.address_state = value["state"]
                        patient.address_zip = value["zip"]
                    elif hasattr(patient, field):
                        setattr(patient, field, value)
                
                session.commit()
                logger.info(f"Patient updated successfully: {patient_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Database error updating patient: {str(e)}")
            return False

class MongoPatientRepository(PatientRepositoryInterface):
    """MongoDB implementation of patient repository."""
    
    async def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new patient in MongoDB.
        
        Args:
            patient_data: Patient information dictionary
            
        Returns:
            Created patient data
            
        Raises:
            ValueError: If duplicate email or phone exists
            RuntimeError: If database operation fails
        """
        try:
            collection = db_manager.get_mongo_collection("patients")
            
            # Create document
            document = PatientDocument.create_document(
                first_name=patient_data["first_name"],
                last_name=patient_data["last_name"],
                email=patient_data["email"],
                phone_number=patient_data["phone_number"],
                password_hash=patient_data["password_hash"],
                date_of_birth=patient_data["date_of_birth"].isoformat(),
                gender=patient_data["gender"],
                address=patient_data["address"],
                emergency_contact=patient_data.get("emergency_contact"),
                medical_history=patient_data.get("medical_history"),
                insurance_info=patient_data.get("insurance_info"),
                email_verified=False,
                phone_verified=False,
                is_active=True
            )
            
            # Insert document
            result = collection.insert_one(document)
            
            # Retrieve created document
            created_document = collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"Patient created successfully with ID: {str(result.inserted_id)}")
            return PatientDocument.to_dict(created_document)
            
        except DuplicateKeyError as e:
            # Determine which field caused the duplicate
            error_message = str(e).lower()
            if "email" in error_message:
                raise ValueError("Email address is already registered")
            elif "phone" in error_message:
                raise ValueError("Phone number is already registered")
            else:
                raise ValueError("Duplicate entry detected")
        except PyMongoError as e:
            logger.error(f"Database error creating patient: {str(e)}")
            raise RuntimeError("Failed to create patient due to database error")
    
    async def get_patient_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get patient by email from MongoDB."""
        try:
            collection = db_manager.get_mongo_collection("patients")
            document = collection.find_one({"email": email})
            return PatientDocument.to_dict(document) if document else None
        except PyMongoError as e:
            logger.error(f"Database error getting patient by email: {str(e)}")
            return None
    
    async def get_patient_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get patient by phone number from MongoDB."""
        try:
            collection = db_manager.get_mongo_collection("patients")
            document = collection.find_one({"phone_number": phone_number})
            return PatientDocument.to_dict(document) if document else None
        except PyMongoError as e:
            logger.error(f"Database error getting patient by phone: {str(e)}")
            return None
    
    async def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by ID from MongoDB."""
        try:
            from bson import ObjectId
            collection = db_manager.get_mongo_collection("patients")
            document = collection.find_one({"_id": ObjectId(patient_id)})
            return PatientDocument.to_dict(document) if document else None
        except (PyMongoError, Exception) as e:
            logger.error(f"Database error getting patient by ID: {str(e)}")
            return None
    
    async def update_patient(self, patient_id: str, update_data: Dict[str, Any]) -> bool:
        """Update patient information in MongoDB."""
        try:
            from bson import ObjectId
            collection = db_manager.get_mongo_collection("patients")
            
            # Convert update data to MongoDB format
            mongo_update_data = update_data.copy()
            
            result = collection.update_one(
                {"_id": ObjectId(patient_id)},
                {"$set": mongo_update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Patient updated successfully: {patient_id}")
                return True
            return False
                
        except (PyMongoError, Exception) as e:
            logger.error(f"Database error updating patient: {str(e)}")
            return False

def get_patient_repository() -> PatientRepositoryInterface:
    """
    Factory function to get the appropriate patient repository based on configuration.
    
    Returns:
        Patient repository instance
    """
    if config.DATABASE_TYPE == DatabaseType.MONGODB:
        return MongoPatientRepository()
    else:
        return SQLPatientRepository() 