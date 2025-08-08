import os
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
import logging

from app.config import config, DatabaseType
from app.models.sql_models import Base
from app.models.nosql_models import ProviderDocument, ProviderAvailabilityDocument, AppointmentSlotDocument, PatientDocument

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages database connections for both SQL and NoSQL databases.
    """
    
    def __init__(self):
        self.database_type = config.DATABASE_TYPE
        self._sql_engine = None
        self._sql_session_factory = None
        self._mongo_client = None
        self._mongo_database = None
        self._initialized = False
        
    def initialize_sql_database(self):
        """Initialize SQL database connection and create tables."""
        try:
            if self.database_type == DatabaseType.MYSQL:
                database_url = config.MYSQL_URL
            elif self.database_type == DatabaseType.POSTGRESQL:
                database_url = config.POSTGRESQL_URL
            else:
                raise ValueError(f"Invalid SQL database type: {self.database_type}")
            
            # For development, use SQLite if other databases are not available
            if "localhost" in database_url and not self._check_database_connection(database_url):
                logger.warning(f"Cannot connect to {self.database_type}, falling back to SQLite")
                database_url = "sqlite:///./healthfirst.db"
            
            self._sql_engine = create_engine(
                database_url,
                echo=config.DEBUG,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Create tables
            Base.metadata.create_all(bind=self._sql_engine)
            
            # Create session factory
            self._sql_session_factory = sessionmaker(
                bind=self._sql_engine,
                autocommit=False,
                autoflush=False
            )
            
            logger.info(f"SQL database initialized successfully with {database_url}")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize SQL database: {str(e)}")
            # Fall back to SQLite for development
            try:
                logger.info("Attempting SQLite fallback...")
                database_url = "sqlite:///./healthfirst.db"
                self._sql_engine = create_engine(database_url, echo=config.DEBUG)
                Base.metadata.create_all(bind=self._sql_engine)
                self._sql_session_factory = sessionmaker(bind=self._sql_engine, autocommit=False, autoflush=False)
                logger.info("SQLite fallback successful")
            except Exception as fallback_error:
                logger.error(f"SQLite fallback also failed: {str(fallback_error)}")
                raise
    
    def _check_database_connection(self, database_url: str) -> bool:
        """Check if database is accessible."""
        try:
            test_engine = create_engine(database_url)
            with test_engine.connect() as conn:
                conn.execute("SELECT 1")
            test_engine.dispose()
            return True
        except Exception:
            return False
    
    def initialize_mongo_database(self):
        """Initialize MongoDB connection and setup collections."""
        try:
            # Try to connect to MongoDB
            self._mongo_client = MongoClient(config.MONGODB_URL, serverSelectionTimeoutMS=5000)
            # Test connection
            self._mongo_client.admin.command('ping')
            
            self._mongo_database = self._mongo_client[config.MONGODB_DATABASE]
            
            # Initialize providers collection
            providers_collection = self._mongo_database.providers
            self._create_collection_indexes(providers_collection, ProviderDocument.get_collection_indexes())
            
            # Initialize patients collection
            patients_collection = self._mongo_database.patients
            self._create_collection_indexes(patients_collection, PatientDocument.get_collection_indexes())
            
            # Initialize provider availability collection
            availability_collection = self._mongo_database.provider_availability
            self._create_collection_indexes(availability_collection, ProviderAvailabilityDocument.get_collection_indexes())
            
            # Initialize appointment slots collection
            slots_collection = self._mongo_database.appointment_slots
            self._create_collection_indexes(slots_collection, AppointmentSlotDocument.get_collection_indexes())
            
            # Set up collection validation for providers
            try:
                validation_schema = ProviderDocument.get_validation_schema()
                self._mongo_database.command(
                    "collMod",
                    "providers",
                    validator=validation_schema
                )
            except PyMongoError as e:
                logger.warning(f"Failed to set collection validation: {str(e)}")
            
            logger.info("MongoDB database initialized successfully")
            
        except PyMongoError as e:
            logger.error(f"Failed to initialize MongoDB: {str(e)}")
            logger.warning("Running without MongoDB - some features may not work")
            # Don't raise the error, allow app to continue without MongoDB
    
    def _create_collection_indexes(self, collection: Collection, index_specs: list):
        """Helper method to create indexes for a collection."""
        for index_spec in index_specs:
            try:
                collection.create_index(
                    index_spec["key"],
                    unique=index_spec.get("unique", False),
                    sparse=index_spec.get("sparse", False),
                    name=index_spec["name"]
                )
            except PyMongoError as e:
                if "already exists" not in str(e):
                    logger.warning(f"Failed to create index {index_spec['name']}: {str(e)}")
    
    def initialize(self):
        """Initialize the appropriate database based on configuration."""
        try:
            if self.database_type == DatabaseType.MONGODB:
                self.initialize_mongo_database()
            else:
                self.initialize_sql_database()
            self._initialized = True
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            logger.warning("App will continue without full database functionality")
            self._initialized = False
    
    @contextmanager
    def get_sql_session(self) -> Generator[Session, None, None]:
        """
        Get SQL database session with automatic cleanup.
        
        Yields:
            SQLAlchemy session
        """
        if not self._sql_session_factory:
            raise RuntimeError("SQL database not initialized")
        
        session = self._sql_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_mongo_collection(self, collection_name: str) -> Collection:
        """
        Get MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            MongoDB collection object
        """
        if not self._mongo_database:
            raise RuntimeError("MongoDB not initialized")
        
        return self._mongo_database[collection_name]
    
    def get_providers_collection(self) -> Collection:
        """Get the providers collection from MongoDB."""
        return self.get_mongo_collection("providers")
    
    def get_patients_collection(self) -> Collection:
        """Get the patients collection from MongoDB."""
        return self.get_mongo_collection("patients")
    
    def get_availability_collection(self) -> Collection:
        """Get the provider availability collection from MongoDB."""
        return self.get_mongo_collection("provider_availability")
    
    def get_appointment_slots_collection(self) -> Collection:
        """Get the appointment slots collection from MongoDB."""
        return self.get_mongo_collection("appointment_slots")
    
    def is_initialized(self) -> bool:
        """Check if database is properly initialized."""
        return self._initialized
    
    def close_connections(self):
        """Close all database connections."""
        if self._sql_engine:
            self._sql_engine.dispose()
            logger.info("SQL database connections closed")
        
        if self._mongo_client:
            self._mongo_client.close()
            logger.info("MongoDB connections closed")

# Global database manager instance
db_manager = DatabaseManager() 