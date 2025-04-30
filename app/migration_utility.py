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
    
    # Track processed users
    processed_users = set()
    
    # Convert and insert into MongoDB
    for user in sql_users:
        # Skip if this is a duplicate email (emails should be unique)
        if user.email in processed_users:
            logger.warning(f"Skipping duplicate user: {user.email}")
            continue
            
        processed_users.add(user.email)
        
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
        
        # Insert into MongoDB using upsert
        result = users_collection.update_one(
            {"email": user.email},
            {"$set": mongo_user},
            upsert=True
        )
        
        # Get the ID
        if result.upserted_id:
            user_id = result.upserted_id
        else:
            doc = users_collection.find_one({"email": user.email})
            user_id = doc["_id"]
        
        # Store the user ID mapping for later use
        id_mapping["users"][user.id] = str(user_id)
    
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
    processed_locations = set()  # Track locations to avoid duplicates
    
    for location in sql_locations:
        # Create a unique key to check for duplicates
        location_key = (location.city, location.street, location.house_number)
        
        # Skip if we've already processed this location
        if location_key in processed_locations:
            logger.warning(f"Skipping duplicate location: {location_key}")
            continue
            
        processed_locations.add(location_key)
        
        mongo_location = {
            "city": location.city,
            "street": location.street,
            "house_number": location.house_number
        }
        
        # Insert into MongoDB using upsert to avoid duplicates
        result = locations_collection.update_one(
            {
                "city": location.city,
                "street": location.street,
                "house_number": location.house_number
            },
            {"$set": mongo_location},
            upsert=True
        )
        
        # Get the ID (either newly inserted or existing)
        if result.upserted_id:
            location_id = result.upserted_id
        else:
            # Find the document to get its ID
            doc = locations_collection.find_one(mongo_location)
            location_id = doc["_id"]
        
        # Store the location ID mapping for later use
        id_mapping["locations"][location.id] = str(location_id)
    
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
    
    # Track processed apartments
    processed_apartments = set()
    
    # Convert and insert into MongoDB
    for apartment in sql_apartments:
        # Skip if this is a duplicate title/owner combination (simple deduplication)
        unique_key = (apartment.title, apartment.owner_id)
        if unique_key in processed_apartments:
            logger.warning(f"Skipping duplicate apartment: {apartment.title} (owner ID: {apartment.owner_id})")
            continue
            
        processed_apartments.add(unique_key)
        
        # Get the location
        location_id = id_mapping["locations"].get(apartment.location_id)
        location = locations_collection.find_one({"_id": location_id}) if location_id else None
        
        # If location not found, create a placeholder
        if not location and apartment.location_id:
            loc = db.query(Location).filter(Location.id == apartment.location_id).first()
            if loc:
                mongo_location = {
                    "city": loc.city,
                    "street": loc.street,
                    "house_number": loc.house_number
                }
                
                # Use upsert to avoid duplicate entries
                result = locations_collection.update_one(
                    mongo_location,
                    {"$set": mongo_location},
                    upsert=True
                )
                
                if result.upserted_id:
                    location_id = result.upserted_id
                else:
                    doc = locations_collection.find_one(mongo_location)
                    location_id = doc["_id"]
                    
                location = locations_collection.find_one({"_id": location_id})
        
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
        
        # Insert into MongoDB using upsert
        result = apartments_collection.update_one(
            {
                "title": apartment.title,
                "owner_id": owner_id
            },
            {"$set": mongo_apartment},
            upsert=True
        )
        
        # Get the ID
        if result.upserted_id:
            apartment_id = result.upserted_id
        else:
            doc = apartments_collection.find_one({"title": apartment.title, "owner_id": owner_id})
            apartment_id = doc["_id"]
            
        # Store the apartment ID mapping for later use
        id_mapping["apartments"][apartment.id] = str(apartment_id)
    
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