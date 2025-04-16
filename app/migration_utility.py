import logging
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from .config import DATABASE_URL, MONGO_URI, MONGO_DB_NAME
from .database import get_db, Base
from .models import User, Apartment, Location
from .database_mongo import get_mongo_db, get_collection
from .models_mongo import convert_object_id, User as MongoUser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("migration")

def check_mysql_tables_exist():
    """Check if required MySQL tables exist"""
    try:
        # Create engine and inspector
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # Check for required tables
        required_tables = ['users', 'apartments', 'locations']
        existing_tables = inspector.get_table_names()
        
        for table in required_tables:
            if table not in existing_tables:
                logger.warning(f"MySQL table '{table}' does not exist")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error checking MySQL tables: {str(e)}")
        return False

def initialize_mongodb_collections():
    """Initialize empty MongoDB collections when MySQL data is not available"""
    logger.info("Initializing empty MongoDB collections...")
    
    # Get collections
    users_collection = get_collection("users")
    apartments_collection = get_collection("apartments")
    locations_collection = get_collection("locations")
    
    # Clear existing data
    users_collection.delete_many({})
    apartments_collection.delete_many({})
    locations_collection.delete_many({})
    
    # Create an admin user
    admin_user = MongoUser.create(
        email="admin@example.com",
        password="admin1234",
        first_name="Admin",
        last_name="User",
        phone="1234567890",
        is_admin=True
    )
    
    users_collection.insert_one(admin_user)
    logger.info("Created default admin user: admin@example.com / admin1234")
    
    logger.info("MongoDB collections initialized with default data")
    return True

def migrate_users():
    """Migrate users from MySQL to MongoDB"""
    logger.info("Starting migration of users...")
    
    # Get MongoDB collection
    users_collection = get_collection("users")
    
    # Clear existing data (optional, comment out if you want to preserve existing MongoDB data)
    users_collection.delete_many({})
    
    # Get SQL session
    db = next(get_db())
    
    # Get all users from SQL
    sql_users = db.query(User).all()
    logger.info(f"Found {len(sql_users)} users in MySQL database")
    
    # Convert and insert into MongoDB
    for user in sql_users:
        mongo_user = {
            "email": user.email,
            "password": user.password,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
        
        # Insert into MongoDB
        result = users_collection.insert_one(mongo_user)
        
        # Store the user ID mapping for later use
        id_mapping["users"][user.id] = str(result.inserted_id)
    
    logger.info(f"Successfully migrated {users_collection.count_documents({})} users to MongoDB")

def migrate_locations():
    """Migrate locations from MySQL to MongoDB"""
    logger.info("Starting migration of locations...")
    
    # Get MongoDB collection
    locations_collection = get_collection("locations")
    
    # Clear existing data
    locations_collection.delete_many({})
    
    # Get SQL session
    db = next(get_db())
    
    # Get all locations from SQL
    sql_locations = db.query(Location).all()
    logger.info(f"Found {len(sql_locations)} locations in MySQL database")
    
    # Convert and insert into MongoDB
    for location in sql_locations:
        mongo_location = {
            "city": location.city,
            "street": location.street,
            "house_number": location.house_number
        }
        
        # Insert into MongoDB
        result = locations_collection.insert_one(mongo_location)
        
        # Store the location ID mapping for later use
        id_mapping["locations"][location.id] = str(result.inserted_id)
    
    logger.info(f"Successfully migrated {locations_collection.count_documents({})} locations to MongoDB")

def migrate_apartments():
    """Migrate apartments from MySQL to MongoDB"""
    logger.info("Starting migration of apartments...")
    
    # Get MongoDB collections
    apartments_collection = get_collection("apartments")
    locations_collection = get_collection("locations")
    
    # Clear existing data
    apartments_collection.delete_many({})
    
    # Get SQL session
    db = next(get_db())
    
    # Get all apartments from SQL
    sql_apartments = db.query(Apartment).all()
    logger.info(f"Found {len(sql_apartments)} apartments in MySQL database")
    
    # Convert and insert into MongoDB
    for apartment in sql_apartments:
        # Get the location
        location_id = id_mapping["locations"].get(apartment.location_id)
        location = locations_collection.find_one({"_id": location_id}) if location_id else None
        
        # If location not found, create a placeholder
        if not location:
            loc = db.query(Location).filter(Location.id == apartment.location_id).first()
            if loc:
                location = {
                    "city": loc.city,
                    "street": loc.street,
                    "house_number": loc.house_number
                }
                result = locations_collection.insert_one(location)
                location["_id"] = result.inserted_id
        
        # Map the owner_id
        owner_id = id_mapping["users"].get(apartment.owner_id)
        moderated_by = id_mapping["users"].get(apartment.moderated_by)
        
        # Create the MongoDB document
        mongo_apartment = {
            "title": apartment.title,
            "description": apartment.description,
            "price": float(apartment.price),
            "owner_id": owner_id,
            "location": convert_object_id(location) if location else None,
            "status": apartment.status,
            "created_at": apartment.created_at,
            "updated_at": apartment.updated_at,
            "moderated_by": moderated_by,
            "moderated_at": apartment.moderated_at
        }
        
        # Insert into MongoDB
        result = apartments_collection.insert_one(mongo_apartment)
        
        # Store the apartment ID mapping for later use
        id_mapping["apartments"][apartment.id] = str(result.inserted_id)
    
    logger.info(f"Successfully migrated {apartments_collection.count_documents({})} apartments to MongoDB")

def run_migration():
    """Run the complete migration process"""
    global id_mapping
    
    # Initialize ID mappings to track SQL IDs to MongoDB IDs
    id_mapping = {
        "users": {},
        "locations": {},
        "apartments": {}
    }
    
    logger.info("Starting database migration from MySQL to MongoDB")
    logger.info(f"Source: {DATABASE_URL}")
    logger.info(f"Target: {MONGO_URI}/{MONGO_DB_NAME}")
    
    try:
        # Check if MySQL tables exist
        mysql_ready = check_mysql_tables_exist()
        
        if mysql_ready:
            # Run migrations in order (users first, then locations, then apartments)
            migrate_users()
            migrate_locations()
            migrate_apartments()
            logger.info("MySQL to MongoDB migration completed successfully")
        else:
            # Initialize MongoDB with default data
            logger.warning("MySQL tables not found, initializing MongoDB with default data")
            initialize_mongodb_collections()
            logger.info("MongoDB initialization completed successfully")
            
        # Create indexes for MongoDB
        from .create_indexes import create_indexes
        create_indexes()
        
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    run_migration() 