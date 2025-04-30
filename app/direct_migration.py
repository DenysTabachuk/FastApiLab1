import logging
import sys
from .migration_utility import run_migration

# Configure logging for direct migration
logger = logging.getLogger("app.direct_migration")

def migrate_directly():
    """
    Directly migrate data from MySQL to MongoDB using the migration utility.
    This function is called from run_direct_migration.py.
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    logger.info("Starting direct migration from MySQL to MongoDB...")
    
    try:
        # Use the existing migration utility to perform the migration
        success = run_migration()
        
        if success:
            logger.info("Direct migration completed successfully")
        else:
            logger.error("Direct migration failed")
            
        return success
    except Exception as e:
        logger.error(f"Error during direct migration: {e}", exc_info=True)
        return False 