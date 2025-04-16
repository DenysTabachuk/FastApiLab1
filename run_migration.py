import logging
import sys
from app.migration_utility import run_migration

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting data migration from MySQL to MongoDB...")
    
    try:
        success = run_migration()
        
        if success:
            logger.info("Migration completed successfully!")
            logger.info("You can now run the application with MongoDB using: python run_mongo.py")
        else:
            logger.error("Migration failed. Please check migration.log for details.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        logger.info("MongoDB will be initialized with default data when you run the application.")
        logger.info("You can run the application with MongoDB using: python run_mongo.py") 