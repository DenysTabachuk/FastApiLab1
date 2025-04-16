"""
Script to migrate data from MySQL to PostgreSQL.
This should be run once to set up the PostgreSQL database and migrate existing data.
"""

import logging
from app.pg_migrate import run_migration

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("migration.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting migration process")
    
    # Run the migration
    success = run_migration()
    
    if success:
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed") 