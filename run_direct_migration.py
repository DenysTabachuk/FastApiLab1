import logging
import sys
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("direct_migration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("run_direct_migration")

def import_config():
    """Import only the config.py file to get the connection strings"""
    try:
        config_path = Path(__file__).parent / "app" / "config.py"
        spec = importlib.util.spec_from_file_location("config", config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        return config
    except Exception as e:
        logger.error(f"Error importing config: {e}")
        return None

def run_migration():
    """Run the direct migration from MySQL to MongoDB"""
    try:
        # Import config to get connection strings
        config = import_config()
        if not config:
            logger.error("Failed to import config")
            return False
            
        from sqlalchemy import create_engine, inspect
        
        # Check MySQL connection
        logger.info(f"Checking MySQL connection: {config.DATABASE_URL}")
        try:
            engine = create_engine(config.DATABASE_URL)
            connection = engine.connect()
            connection.close()
            logger.info("MySQL connection successful")
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            
        # Import and run direct migration
        from app.direct_migration import migrate_directly
        
        success = migrate_directly()
        if success:
            logger.info("Direct migration completed successfully")
            logger.info("You can now run the MongoDB version of the application")
            logger.info("Run 'python run_mongo.py' to start the application")
        else:
            logger.error("Direct migration failed")
            
        return success
    except Exception as e:
        logger.error(f"Error during direct migration: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting direct migration from MySQL to MongoDB...")
    run_migration() 