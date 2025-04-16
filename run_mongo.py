import uvicorn
import logging
import sys
from app.database_mongo import get_mongo_db
from app.create_indexes import create_indexes
from app.models_mongo import User

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mongodb.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def initialize_mongodb_if_empty():
    """Initialize MongoDB with an admin user if users collection is empty"""
    try:
        from app.database_mongo import get_collection
        users_collection = get_collection("users")
        
        if users_collection.count_documents({}) == 0:
            logger.info("Users collection is empty, creating default admin user")
            admin_user = {
                "email": "admin@example.com",
                "password": "admin1234",
                "first_name": "Admin",
                "last_name": "User",
                "phone": "1234567890",
                "is_admin": True,
                "is_active": True
            }
            users_collection.insert_one(admin_user)
            logger.info("Created default admin user: admin@example.com / admin1234")
        
        # Create indexes
        create_indexes()
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        return False

if __name__ == "__main__":
    # Check MongoDB connection
    try:
        db = get_mongo_db()
        logger.info("Successfully connected to MongoDB")
        
        # Initialize if needed
        initialize_mongodb_if_empty()
        
        # Start FastAPI application with MongoDB
        logger.info("Starting FastAPI application with MongoDB...")
        uvicorn.run("app.main_mongo:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.error("Please make sure MongoDB is running and accessible.") 