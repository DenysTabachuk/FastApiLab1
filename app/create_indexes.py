import logging
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure
from .database_mongo import get_mongo_db, get_collection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_indexes():
    """Create indexes for MongoDB collections"""
    try:
        # Get collections
        users_collection = get_collection("users")
        apartments_collection = get_collection("apartments")
        locations_collection = get_collection("locations")
        
        logger.info("Creating MongoDB indexes...")
        
        # User indexes
        logger.info("Creating indexes for users collection...")
        users_collection.create_index("email", unique=True)
        users_collection.create_index("is_active")
        users_collection.create_index("is_admin")
        
        # Apartment indexes
        logger.info("Creating indexes for apartments collection...")
        apartments_collection.create_index("owner_id")
        apartments_collection.create_index("status")
        apartments_collection.create_index("created_at")
        apartments_collection.create_index("price")
        apartments_collection.create_index([("price", ASCENDING), ("created_at", DESCENDING)])
        
        # Text search index for apartments
        apartments_collection.create_index([
            ("title", TEXT), 
            ("description", TEXT),
            ("location.city", TEXT),
            ("location.street", TEXT)
        ], 
        name="text_search_index", 
        default_language="english",
        weights={
            "title": 10,
            "description": 5,
            "location.city": 3,
            "location.street": 1
        })
        
        # Location indexes
        logger.info("Creating indexes for locations collection...")
        locations_collection.create_index([
            ("city", ASCENDING),
            ("street", ASCENDING),
            ("house_number", ASCENDING)
        ], unique=True)
        
        logger.info("MongoDB indexes created successfully")
        return True
    except OperationFailure as e:
        logger.error(f"Failed to create indexes: {e}")
        return False

if __name__ == "__main__":
    create_indexes() 