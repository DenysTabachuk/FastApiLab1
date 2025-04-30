import logging
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure
from .database_mongo import get_mongo_db, get_collection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_indexes():
    """Create MongoDB indexes for better performance"""
    logger.info("Creating MongoDB indexes...")
    
    try:
        # Users collection indexes
        logger.info("Creating indexes for users collection...")
        users_collection = get_collection("users")
        users_collection.create_index("email", unique=True)
        
        # Apartments collection indexes
        logger.info("Creating indexes for apartments collection...")
        apartments_collection = get_collection("apartments")
        apartments_collection.create_index("owner_id")
        apartments_collection.create_index("status")
        # Text search index
        apartments_collection.create_index([("title", "text"), ("description", "text")])
        
        # Locations collection indexes
        logger.info("Creating indexes for locations collection...")
        locations_collection = get_collection("locations")
        locations_collection.create_index([("city", 1), ("street", 1), ("house_number", 1)], unique=True)
        
        # Apartment observations collection indexes
        logger.info("Creating indexes for apartment observations collection...")
        observations_collection = get_collection("apartment_observations")
        observations_collection.create_index([("user_id", 1), ("apartment_id", 1)], unique=True)
        observations_collection.create_index("user_id")
        
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {e}")
        raise

if __name__ == "__main__":
    create_indexes() 