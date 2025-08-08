import os
from enum import Enum
from typing import Optional

class DatabaseType(str, Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"

class Config:
    # Application settings
    APP_NAME = "Health First Provider Registration"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
    
    # Database settings
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "postgresql")
    
    # SQL Database URLs
    MYSQL_URL = os.getenv("MYSQL_URL", "mysql+pymysql://user:password@localhost:3306/healthfirst")
    POSTGRESQL_URL = os.getenv("POSTGRESQL_URL", "postgresql+psycopg2://user:password@localhost:5432/healthfirst")
    
    # MongoDB settings
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "healthfirst")
    
    # Validation settings
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 100
    
    # Provider settings
    PREDEFINED_SPECIALIZATIONS = [
        "Cardiology", "Dermatology", "Endocrinology", "Gastroenterology",
        "Neurology", "Oncology", "Orthopedics", "Pediatrics", "Psychiatry",
        "Pulmonology", "Radiology", "Surgery", "Urology", "Emergency Medicine",
        "Family Medicine", "Internal Medicine", "Obstetrics and Gynecology"
    ]

config = Config() 