from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pymongo.errors import DuplicateKeyError, PyMongoError
import logging

from app.config import config, DatabaseType
from app.database.connections import db_manager
from app.models.sql_models import Provider
from app.models.nosql_models import ProviderDocument
from app.schemas.provider import VerificationStatus

logger = logging.getLogger(__name__)

class ProviderRepositoryInterface(ABC):
    """Abstract interface for provider repository operations."""
    
    @abstractmethod
    async def create_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new provider."""
        pass
    
    @abstractmethod
    async def get_provider_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get provider by email."""
        pass
    
    @abstractmethod
    async def get_provider_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get provider by phone number."""
        pass
    
    @abstractmethod
    async def get_provider_by_license(self, license_number: str) -> Optional[Dict[str, Any]]:
        """Get provider by license number."""
        pass
    
    @abstractmethod
    async def get_provider_by_id(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider by ID."""
        pass

class SQLProviderRepository(ProviderRepositoryInterface):
    """SQL implementation of provider repository."""
    
    async def create_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new provider in SQL database.
        
        Args:
            provider_data: Provider information dictionary
            
        Returns:
            Created provider data
            
        Raises:
            ValueError: If duplicate email, phone, or license exists
            RuntimeError: If database operation fails
        """
        try:
            with db_manager.get_sql_session() as session:
                # Create provider instance
                provider = Provider(
                    first_name=provider_data["first_name"],
                    last_name=provider_data["last_name"],
                    email=provider_data["email"],
                    phone_number=provider_data["phone_number"],
                    password_hash=provider_data["password_hash"],
                    specialization=provider_data["specialization"],
                    license_number=provider_data["license_number"],
                    years_of_experience=provider_data["years_of_experience"],
                    clinic_street=provider_data["clinic_address"]["street"],
                    clinic_city=provider_data["clinic_address"]["city"],
                    clinic_state=provider_data["clinic_address"]["state"],
                    clinic_zip=provider_data["clinic_address"]["zip"],
                    verification_status=VerificationStatus.PENDING,
                    is_active=True
                )
                
                session.add(provider)
                session.flush()  # Get the ID without committing
                
                result = provider.to_dict()
                session.commit()
                
                logger.info(f"Provider created successfully with ID: {result['provider_id']}")
                return result
                
        except IntegrityError as e:
            error_message = str(e.orig).lower()
            if "email" in error_message:
                raise ValueError("Email address is already registered")
            elif "phone" in error_message:
                raise ValueError("Phone number is already registered")
            elif "license" in error_message:
                raise ValueError("License number is already registered")
            else:
                raise ValueError("Duplicate entry detected")
        except SQLAlchemyError as e:
            logger.error(f"Database error creating provider: {str(e)}")
            raise RuntimeError("Failed to create provider due to database error")
    
    async def get_provider_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get provider by email from SQL database."""
        try:
            with db_manager.get_sql_session() as session:
                provider = session.query(Provider).filter(Provider.email == email).first()
                return provider.to_dict() if provider else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting provider by email: {str(e)}")
            return None
    
    async def get_provider_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get provider by phone number from SQL database."""
        try:
            with db_manager.get_sql_session() as session:
                provider = session.query(Provider).filter(Provider.phone_number == phone_number).first()
                return provider.to_dict() if provider else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting provider by phone: {str(e)}")
            return None
    
    async def get_provider_by_license(self, license_number: str) -> Optional[Dict[str, Any]]:
        """Get provider by license number from SQL database."""
        try:
            with db_manager.get_sql_session() as session:
                provider = session.query(Provider).filter(Provider.license_number == license_number).first()
                return provider.to_dict() if provider else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting provider by license: {str(e)}")
            return None
    
    async def get_provider_by_id(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider by ID from SQL database."""
        try:
            with db_manager.get_sql_session() as session:
                provider = session.query(Provider).filter(Provider.id == provider_id).first()
                return provider.to_dict() if provider else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting provider by ID: {str(e)}")
            return None

class MongoProviderRepository(ProviderRepositoryInterface):
    """MongoDB implementation of provider repository."""
    
    async def create_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new provider in MongoDB.
        
        Args:
            provider_data: Provider information dictionary
            
        Returns:
            Created provider data
            
        Raises:
            ValueError: If duplicate email, phone, or license exists
            RuntimeError: If database operation fails
        """
        try:
            collection = db_manager.get_providers_collection()
            
            # Create document
            document = ProviderDocument.create_document(
                first_name=provider_data["first_name"],
                last_name=provider_data["last_name"],
                email=provider_data["email"],
                phone_number=provider_data["phone_number"],
                password_hash=provider_data["password_hash"],
                specialization=provider_data["specialization"],
                license_number=provider_data["license_number"],
                years_of_experience=provider_data["years_of_experience"],
                clinic_address=provider_data["clinic_address"]
            )
            
            # Insert document
            result = collection.insert_one(document)
            
            # Retrieve created document
            created_document = collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"Provider created successfully with ID: {str(result.inserted_id)}")
            return ProviderDocument.to_dict(created_document)
            
        except DuplicateKeyError as e:
            # Determine which field caused the duplicate
            error_message = str(e).lower()
            if "email" in error_message:
                raise ValueError("Email address is already registered")
            elif "phone" in error_message:
                raise ValueError("Phone number is already registered")
            elif "license" in error_message:
                raise ValueError("License number is already registered")
            else:
                raise ValueError("Duplicate entry detected")
        except PyMongoError as e:
            logger.error(f"Database error creating provider: {str(e)}")
            raise RuntimeError("Failed to create provider due to database error")
    
    async def get_provider_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get provider by email from MongoDB."""
        try:
            collection = db_manager.get_providers_collection()
            document = collection.find_one({"email": email})
            return ProviderDocument.to_dict(document) if document else None
        except PyMongoError as e:
            logger.error(f"Database error getting provider by email: {str(e)}")
            return None
    
    async def get_provider_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get provider by phone number from MongoDB."""
        try:
            collection = db_manager.get_providers_collection()
            document = collection.find_one({"phone_number": phone_number})
            return ProviderDocument.to_dict(document) if document else None
        except PyMongoError as e:
            logger.error(f"Database error getting provider by phone: {str(e)}")
            return None
    
    async def get_provider_by_license(self, license_number: str) -> Optional[Dict[str, Any]]:
        """Get provider by license number from MongoDB."""
        try:
            collection = db_manager.get_providers_collection()
            document = collection.find_one({"license_number": license_number})
            return ProviderDocument.to_dict(document) if document else None
        except PyMongoError as e:
            logger.error(f"Database error getting provider by license: {str(e)}")
            return None
    
    async def get_provider_by_id(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider by ID from MongoDB."""
        try:
            from bson import ObjectId
            collection = db_manager.get_providers_collection()
            document = collection.find_one({"_id": ObjectId(provider_id)})
            return ProviderDocument.to_dict(document) if document else None
        except (PyMongoError, Exception) as e:
            logger.error(f"Database error getting provider by ID: {str(e)}")
            return None

def get_provider_repository() -> ProviderRepositoryInterface:
    """
    Factory function to get the appropriate provider repository based on configuration.
    
    Returns:
        Provider repository instance
    """
    if config.DATABASE_TYPE == DatabaseType.MONGODB:
        return MongoProviderRepository()
    else:
        return SQLProviderRepository() 