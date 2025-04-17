"""
Script to update the full-text search configuration from 'english' to 'russian'
for better support of Cyrillic characters.
"""
import os
import sys

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_psycopg_conn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_search_config():
    """Update the PostgreSQL full-text search configuration"""
    logger.info("Updating full-text search configuration from 'english' to 'russian'")
    
    conn = None
    try:
        conn = get_psycopg_conn()
        cursor = conn.cursor()
        
        # Update the trigger function
        cursor.execute("""
        CREATE OR REPLACE FUNCTION apartments_search_vector_update() RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector = 
                setweight(to_tsvector('russian', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('russian', COALESCE(NEW.description, '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        # Update existing records
        cursor.execute("""
        UPDATE apartments SET 
        search_vector = setweight(to_tsvector('russian', COALESCE(title, '')), 'A') ||
                        setweight(to_tsvector('russian', COALESCE(description, '')), 'B');
        """)
        
        conn.commit()
        logger.info("Full-text search configuration updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating search configuration: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_search_config() 