from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pymongo.errors import DuplicateKeyError, PyMongoError
import logging

from app.config import config, DatabaseType
from app.database.connections import db_manager
from app.models.sql_models import ProviderAvailability, AppointmentSlot, Patient
from app.models.nosql_models import ProviderAvailabilityDocument, AppointmentSlotDocument, PatientDocument

logger = logging.getLogger(__name__)

class AvailabilityRepositoryInterface(ABC):
    """Abstract interface for availability repository operations."""
    
    @abstractmethod
    async def create_availability(self, availability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new provider availability."""
        pass
    
    @abstractmethod
    async def get_availability_by_id(self, availability_id: str) -> Optional[Dict[str, Any]]:
        """Get availability by ID."""
        pass
    
    @abstractmethod
    async def get_provider_availability(self, provider_id: str, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """Get availability for a provider within date range."""
        pass
    
    @abstractmethod
    async def update_availability(self, availability_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update availability record."""
        pass
    
    @abstractmethod
    async def delete_availability(self, availability_id: str) -> bool:
        """Delete availability record."""
        pass
    
    @abstractmethod
    async def create_appointment_slot(self, slot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new appointment slot."""
        pass
    
    @abstractmethod
    async def get_appointment_slots(self, availability_id: str) -> List[Dict[str, Any]]:
        """Get all slots for an availability."""
        pass
    
    @abstractmethod
    async def get_available_slots(self, provider_id: str, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """Get available slots for a provider within date range."""
        pass
    
    @abstractmethod
    async def update_slot_status(self, slot_id: str, status: str, patient_id: str = None) -> Optional[Dict[str, Any]]:
        """Update slot status and patient assignment."""
        pass

class SQLAvailabilityRepository(AvailabilityRepositoryInterface):
    """SQL implementation of availability repository."""
    
    async def create_availability(self, availability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new provider availability."""
        try:
            with db_manager.get_sql_session() as session:
                availability = ProviderAvailability(**availability_data)
                session.add(availability)
                session.commit()
                session.refresh(availability)
                
                logger.info(f"Availability created successfully with ID: {availability.id}")
                
                # Convert to dict format
                result = {
                    "availability_id": str(availability.id),
                    "provider_id": availability.provider_id,
                    "date": availability.date,
                    "start_time": availability.start_time,
                    "end_time": availability.end_time,
                    "timezone": availability.timezone,
                    "is_recurring": availability.is_recurring,
                    "recurrence_pattern": availability.recurrence_pattern.value if availability.recurrence_pattern else None,
                    "recurrence_end_date": availability.recurrence_end_date,
                    "slot_duration": availability.slot_duration,
                    "break_duration": availability.break_duration,
                    "max_appointments_per_slot": availability.max_appointments_per_slot,
                    "current_appointments": availability.current_appointments,
                    "appointment_type": availability.appointment_type.value,
                    "status": availability.status.value,
                    "location": availability.location,
                    "pricing": availability.pricing,
                    "notes": availability.notes,
                    "special_requirements": availability.special_requirements or [],
                    "created_at": availability.created_at,
                    "updated_at": availability.updated_at
                }
                
                return result
                
        except IntegrityError as e:
            logger.error(f"Integrity error creating availability: {str(e)}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error creating availability: {str(e)}")
            raise
    
    async def get_availability_by_id(self, availability_id: str) -> Optional[Dict[str, Any]]:
        """Get availability by ID."""
        try:
            with db_manager.get_sql_session() as session:
                availability = session.query(ProviderAvailability).filter(
                    ProviderAvailability.id == availability_id
                ).first()
                
                if availability:
                    return {
                        "availability_id": str(availability.id),
                        "provider_id": availability.provider_id,
                        "date": availability.date,
                        "start_time": availability.start_time,
                        "end_time": availability.end_time,
                        "timezone": availability.timezone,
                        "is_recurring": availability.is_recurring,
                        "recurrence_pattern": availability.recurrence_pattern.value if availability.recurrence_pattern else None,
                        "recurrence_end_date": availability.recurrence_end_date,
                        "slot_duration": availability.slot_duration,
                        "break_duration": availability.break_duration,
                        "max_appointments_per_slot": availability.max_appointments_per_slot,
                        "current_appointments": availability.current_appointments,
                        "appointment_type": availability.appointment_type.value,
                        "status": availability.status.value,
                        "location": availability.location,
                        "pricing": availability.pricing,
                        "notes": availability.notes,
                        "special_requirements": availability.special_requirements or [],
                        "created_at": availability.created_at,
                        "updated_at": availability.updated_at
                    }
                
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting availability: {str(e)}")
            return None
    
    async def get_provider_availability(self, provider_id: str, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """Get availability for a provider within date range."""
        try:
            with db_manager.get_sql_session() as session:
                query = session.query(ProviderAvailability).filter(
                    ProviderAvailability.provider_id == provider_id
                )
                
                if start_date:
                    query = query.filter(ProviderAvailability.date >= start_date)
                if end_date:
                    query = query.filter(ProviderAvailability.date <= end_date)
                
                availabilities = query.order_by(ProviderAvailability.date, ProviderAvailability.start_time).all()
                
                result = []
                for availability in availabilities:
                    result.append({
                        "availability_id": str(availability.id),
                        "provider_id": availability.provider_id,
                        "date": availability.date,
                        "start_time": availability.start_time,
                        "end_time": availability.end_time,
                        "timezone": availability.timezone,
                        "is_recurring": availability.is_recurring,
                        "recurrence_pattern": availability.recurrence_pattern.value if availability.recurrence_pattern else None,
                        "recurrence_end_date": availability.recurrence_end_date,
                        "slot_duration": availability.slot_duration,
                        "break_duration": availability.break_duration,
                        "max_appointments_per_slot": availability.max_appointments_per_slot,
                        "current_appointments": availability.current_appointments,
                        "appointment_type": availability.appointment_type.value,
                        "status": availability.status.value,
                        "location": availability.location,
                        "pricing": availability.pricing,
                        "notes": availability.notes,
                        "special_requirements": availability.special_requirements or [],
                        "created_at": availability.created_at,
                        "updated_at": availability.updated_at
                    })
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting provider availability: {str(e)}")
            return []
    
    async def update_availability(self, availability_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update availability record."""
        try:
            with db_manager.get_sql_session() as session:
                availability = session.query(ProviderAvailability).filter(
                    ProviderAvailability.id == availability_id
                ).first()
                
                if not availability:
                    return None
                
                # Update fields
                for key, value in update_data.items():
                    if hasattr(availability, key) and value is not None:
                        setattr(availability, key, value)
                
                availability.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(availability)
                
                return await self.get_availability_by_id(availability_id)
                
        except SQLAlchemyError as e:
            logger.error(f"Database error updating availability: {str(e)}")
            return None
    
    async def delete_availability(self, availability_id: str) -> bool:
        """Delete availability record."""
        try:
            with db_manager.get_sql_session() as session:
                # First delete associated slots
                session.query(AppointmentSlot).filter(
                    AppointmentSlot.availability_id == availability_id
                ).delete()
                
                # Then delete availability
                deleted_count = session.query(ProviderAvailability).filter(
                    ProviderAvailability.id == availability_id
                ).delete()
                
                session.commit()
                return deleted_count > 0
                
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting availability: {str(e)}")
            return False
    
    async def create_appointment_slot(self, slot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new appointment slot."""
        try:
            with db_manager.get_sql_session() as session:
                slot = AppointmentSlot(**slot_data)
                session.add(slot)
                session.commit()
                session.refresh(slot)
                
                return {
                    "slot_id": str(slot.id),
                    "availability_id": slot.availability_id,
                    "provider_id": slot.provider_id,
                    "patient_id": slot.patient_id,
                    "slot_start_time": slot.slot_start_time,
                    "slot_end_time": slot.slot_end_time,
                    "status": slot.status.value,
                    "appointment_type": slot.appointment_type,
                    "booking_reference": slot.booking_reference,
                    "patient_notes": slot.patient_notes,
                    "special_instructions": slot.special_instructions,
                    "created_at": slot.created_at,
                    "updated_at": slot.updated_at,
                    "booked_at": slot.booked_at
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Database error creating appointment slot: {str(e)}")
            raise
    
    async def get_appointment_slots(self, availability_id: str) -> List[Dict[str, Any]]:
        """Get all slots for an availability."""
        try:
            with db_manager.get_sql_session() as session:
                slots = session.query(AppointmentSlot).filter(
                    AppointmentSlot.availability_id == availability_id
                ).order_by(AppointmentSlot.slot_start_time).all()
                
                result = []
                for slot in slots:
                    result.append({
                        "slot_id": str(slot.id),
                        "availability_id": slot.availability_id,
                        "provider_id": slot.provider_id,
                        "patient_id": slot.patient_id,
                        "slot_start_time": slot.slot_start_time,
                        "slot_end_time": slot.slot_end_time,
                        "status": slot.status.value,
                        "appointment_type": slot.appointment_type,
                        "booking_reference": slot.booking_reference,
                        "patient_notes": slot.patient_notes,
                        "special_instructions": slot.special_instructions,
                        "created_at": slot.created_at,
                        "updated_at": slot.updated_at,
                        "booked_at": slot.booked_at
                    })
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting appointment slots: {str(e)}")
            return []
    
    async def get_available_slots(self, provider_id: str, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """Get available slots for a provider within date range."""
        try:
            with db_manager.get_sql_session() as session:
                query = session.query(AppointmentSlot).filter(
                    AppointmentSlot.provider_id == provider_id,
                    AppointmentSlot.status == 'available'
                )
                
                if start_date:
                    start_datetime = datetime.combine(start_date, datetime.min.time())
                    query = query.filter(AppointmentSlot.slot_start_time >= start_datetime)
                
                if end_date:
                    end_datetime = datetime.combine(end_date, datetime.max.time())
                    query = query.filter(AppointmentSlot.slot_start_time <= end_datetime)
                
                slots = query.order_by(AppointmentSlot.slot_start_time).all()
                
                result = []
                for slot in slots:
                    result.append({
                        "slot_id": str(slot.id),
                        "availability_id": slot.availability_id,
                        "provider_id": slot.provider_id,
                        "patient_id": slot.patient_id,
                        "slot_start_time": slot.slot_start_time,
                        "slot_end_time": slot.slot_end_time,
                        "status": slot.status.value,
                        "appointment_type": slot.appointment_type,
                        "booking_reference": slot.booking_reference,
                        "patient_notes": slot.patient_notes,
                        "special_instructions": slot.special_instructions,
                        "created_at": slot.created_at,
                        "updated_at": slot.updated_at,
                        "booked_at": slot.booked_at
                    })
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting available slots: {str(e)}")
            return []
    
    async def update_slot_status(self, slot_id: str, status: str, patient_id: str = None) -> Optional[Dict[str, Any]]:
        """Update slot status and patient assignment."""
        try:
            with db_manager.get_sql_session() as session:
                slot = session.query(AppointmentSlot).filter(
                    AppointmentSlot.id == slot_id
                ).first()
                
                if not slot:
                    return None
                
                slot.status = status
                if patient_id:
                    slot.patient_id = patient_id
                    slot.booked_at = datetime.utcnow()
                slot.updated_at = datetime.utcnow()
                
                session.commit()
                session.refresh(slot)
                
                return {
                    "slot_id": str(slot.id),
                    "availability_id": slot.availability_id,
                    "provider_id": slot.provider_id,
                    "patient_id": slot.patient_id,
                    "slot_start_time": slot.slot_start_time,
                    "slot_end_time": slot.slot_end_time,
                    "status": slot.status.value,
                    "appointment_type": slot.appointment_type,
                    "booking_reference": slot.booking_reference,
                    "patient_notes": slot.patient_notes,
                    "special_instructions": slot.special_instructions,
                    "created_at": slot.created_at,
                    "updated_at": slot.updated_at,
                    "booked_at": slot.booked_at
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Database error updating slot status: {str(e)}")
            return None

class MongoAvailabilityRepository(AvailabilityRepositoryInterface):
    """MongoDB implementation of availability repository."""
    
    async def create_availability(self, availability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new provider availability."""
        try:
            collection = db_manager.get_availability_collection()
            document = ProviderAvailabilityDocument.create_document(**availability_data)
            result = collection.insert_one(document)
            
            if result.inserted_id:
                document['_id'] = result.inserted_id
                logger.info(f"Availability created successfully with ID: {result.inserted_id}")
                return ProviderAvailabilityDocument.to_dict(document)
            
            raise Exception("Failed to create availability")
            
        except PyMongoError as e:
            logger.error(f"MongoDB error creating availability: {str(e)}")
            raise
    
    async def get_availability_by_id(self, availability_id: str) -> Optional[Dict[str, Any]]:
        """Get availability by ID."""
        try:
            from bson import ObjectId
            collection = db_manager.get_availability_collection()
            document = collection.find_one({"_id": ObjectId(availability_id)})
            
            if document:
                return ProviderAvailabilityDocument.to_dict(document)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting availability: {str(e)}")
            return None
    
    async def get_provider_availability(self, provider_id: str, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """Get availability for a provider within date range."""
        try:
            collection = db_manager.get_availability_collection()
            query = {"provider_id": provider_id}
            
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = datetime.combine(start_date, datetime.min.time())
                if end_date:
                    date_query["$lte"] = datetime.combine(end_date, datetime.max.time())
                query["date"] = date_query
            
            documents = collection.find(query).sort([("date", 1), ("start_time", 1)])
            
            result = []
            for document in documents:
                result.append(ProviderAvailabilityDocument.to_dict(document))
            
            return result
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting provider availability: {str(e)}")
            return []
    
    async def update_availability(self, availability_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update availability record."""
        try:
            from bson import ObjectId
            collection = db_manager.get_availability_collection()
            
            update_data["updated_at"] = datetime.utcnow()
            result = collection.update_one(
                {"_id": ObjectId(availability_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_availability_by_id(availability_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating availability: {str(e)}")
            return None
    
    async def delete_availability(self, availability_id: str) -> bool:
        """Delete availability record."""
        try:
            from bson import ObjectId
            
            # Delete associated slots first
            slots_collection = db_manager.get_appointment_slots_collection()
            slots_collection.delete_many({"availability_id": availability_id})
            
            # Delete availability
            collection = db_manager.get_availability_collection()
            result = collection.delete_one({"_id": ObjectId(availability_id)})
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting availability: {str(e)}")
            return False
    
    async def create_appointment_slot(self, slot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new appointment slot."""
        try:
            collection = db_manager.get_appointment_slots_collection()
            document = AppointmentSlotDocument.create_document(**slot_data)
            result = collection.insert_one(document)
            
            if result.inserted_id:
                document['_id'] = result.inserted_id
                return AppointmentSlotDocument.to_dict(document)
            
            raise Exception("Failed to create appointment slot")
            
        except PyMongoError as e:
            logger.error(f"MongoDB error creating appointment slot: {str(e)}")
            raise
    
    async def get_appointment_slots(self, availability_id: str) -> List[Dict[str, Any]]:
        """Get all slots for an availability."""
        try:
            collection = db_manager.get_appointment_slots_collection()
            documents = collection.find({"availability_id": availability_id}).sort("slot_start_time", 1)
            
            result = []
            for document in documents:
                result.append(AppointmentSlotDocument.to_dict(document))
            
            return result
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting appointment slots: {str(e)}")
            return []
    
    async def get_available_slots(self, provider_id: str, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """Get available slots for a provider within date range."""
        try:
            collection = db_manager.get_appointment_slots_collection()
            query = {
                "provider_id": provider_id,
                "status": "available"
            }
            
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = datetime.combine(start_date, datetime.min.time())
                if end_date:
                    date_query["$lte"] = datetime.combine(end_date, datetime.max.time())
                query["slot_start_time"] = date_query
            
            documents = collection.find(query).sort("slot_start_time", 1)
            
            result = []
            for document in documents:
                result.append(AppointmentSlotDocument.to_dict(document))
            
            return result
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting available slots: {str(e)}")
            return []
    
    async def update_slot_status(self, slot_id: str, status: str, patient_id: str = None) -> Optional[Dict[str, Any]]:
        """Update slot status and patient assignment."""
        try:
            from bson import ObjectId
            collection = db_manager.get_appointment_slots_collection()
            
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if patient_id:
                update_data["patient_id"] = patient_id
                update_data["booked_at"] = datetime.utcnow()
            
            result = collection.update_one(
                {"_id": ObjectId(slot_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                document = collection.find_one({"_id": ObjectId(slot_id)})
                if document:
                    return AppointmentSlotDocument.to_dict(document)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating slot status: {str(e)}")
            return None

def get_availability_repository() -> AvailabilityRepositoryInterface:
    """
    Factory function to get the appropriate availability repository based on configuration.
    
    Returns:
        Availability repository instance
    """
    if config.DATABASE_TYPE == DatabaseType.MONGODB:
        return MongoAvailabilityRepository()
    else:
        return SQLAvailabilityRepository() 