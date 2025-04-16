"""
Migration script to transfer data from MySQL to PostgreSQL.
This script should be run once to migrate existing data to the new PostgreSQL database.
"""

import logging
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import configurations
from .config import MYSQL_DATABASE_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_PORT, POSTGRES_DB, POSTGRES_DATABASE_URL
from .models import Base

def setup_postgres_db():
    """
    Connect to PostgreSQL and create the database if it doesn't exist
    """
    try:
        # Connect to PostgreSQL server (default database)
        conn = psycopg2.connect(
            host=POSTGRES_SERVER,
            port=POSTGRES_PORT,
            database="postgres",  # Default database
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_DB}'")
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database {POSTGRES_DB}")
            cursor.execute(f"CREATE DATABASE {POSTGRES_DB}")
            logger.info(f"Database {POSTGRES_DB} created successfully")
        else:
            logger.info(f"Database {POSTGRES_DB} already exists")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error setting up PostgreSQL database: {e}")
        return False

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        engine = create_engine(MYSQL_DATABASE_URL)
        Session = sessionmaker(bind=engine)
        return Session(), engine
    except Exception as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None, None

def get_postgres_connection():
    """Get a connection to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_SERVER,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return None

def migrate_users(mysql_session, pg_conn):
    """Migrate users from MySQL to PostgreSQL"""
    logger.info("Starting migration of users")
    try:
        # Get all users from MySQL
        result = mysql_session.execute(text("SELECT * FROM users"))
        users = result.fetchall()
        
        if not users:
            logger.info("No users to migrate")
            return 0
        
        cursor = pg_conn.cursor()
        
        # Clear existing data in PostgreSQL
        cursor.execute("TRUNCATE TABLE users CASCADE")
        
        count = 0
        for user in users:
            # Insert into PostgreSQL with default values for new columns
            cursor.execute("""
            INSERT INTO users (id, email, password, first_name, last_name, phone, is_admin, is_active, created_at, last_login, profile_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '{}')
            """, (
                user.id, user.email, user.password, user.first_name, user.last_name, user.phone,
                user.is_admin, user.is_active, user.created_at, user.last_login
            ))
            count += 1
        
        pg_conn.commit()
        logger.info(f"Migrated {count} users successfully")
        return count
    except Exception as e:
        logger.error(f"Error migrating users: {e}")
        pg_conn.rollback()
        return 0

def migrate_locations(mysql_session, pg_conn):
    """Migrate locations from MySQL to PostgreSQL"""
    logger.info("Starting migration of locations")
    try:
        # Get all locations from MySQL
        result = mysql_session.execute(text("SELECT * FROM locations"))
        locations = result.fetchall()
        
        if not locations:
            logger.info("No locations to migrate")
            return 0
        
        cursor = pg_conn.cursor()
        
        # Clear existing data in PostgreSQL
        cursor.execute("TRUNCATE TABLE locations CASCADE")
        
        count = 0
        for location in locations:
            # Insert into PostgreSQL with default values for new columns
            cursor.execute("""
            INSERT INTO locations (id, city, street, house_number, coordinates)
            VALUES (%s, %s, %s, %s, '{}')
            """, (
                location.id, location.city, location.street, location.house_number
            ))
            count += 1
        
        pg_conn.commit()
        logger.info(f"Migrated {count} locations successfully")
        return count
    except Exception as e:
        logger.error(f"Error migrating locations: {e}")
        pg_conn.rollback()
        return 0

def migrate_apartments(mysql_session, pg_conn):
    """Migrate apartments from MySQL to PostgreSQL"""
    logger.info("Starting migration of apartments")
    try:
        # Get all apartments from MySQL
        result = mysql_session.execute(text("SELECT * FROM apartments"))
        apartments = result.fetchall()
        
        if not apartments:
            logger.info("No apartments to migrate")
            return 0
        
        cursor = pg_conn.cursor()
        
        # Clear existing data in PostgreSQL
        cursor.execute("TRUNCATE TABLE apartments CASCADE")
        
        count = 0
        for apartment in apartments:
            # Insert into PostgreSQL with default values for new columns
            cursor.execute("""
            INSERT INTO apartments (
                id, title, description, price, owner_id, location_id, 
                status, created_at, updated_at, moderated_by, moderated_at,
                features
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '{}')
            """, (
                apartment.id, apartment.title, apartment.description, apartment.price,
                apartment.owner_id, apartment.location_id, apartment.status,
                apartment.created_at, apartment.updated_at, apartment.moderated_by, apartment.moderated_at
            ))
            count += 1
        
        pg_conn.commit()
        logger.info(f"Migrated {count} apartments successfully")
        return count
    except Exception as e:
        logger.error(f"Error migrating apartments: {e}")
        pg_conn.rollback()
        return 0

def create_postgres_triggers(pg_conn):
    """Create PostgreSQL triggers for automatic updates"""
    logger.info("Creating PostgreSQL triggers")
    try:
        cursor = pg_conn.cursor()
        
        # Trigger for automatic update of updated_at field
        cursor.execute("""
        DROP TRIGGER IF EXISTS set_updated_at ON apartments;
        CREATE TRIGGER set_updated_at
        BEFORE UPDATE ON apartments
        FOR EACH ROW
        EXECUTE FUNCTION update_modified_column();
        """)
        
        # Trigger for updating search vector
        cursor.execute("""
        CREATE OR REPLACE FUNCTION apartments_search_vector_update() RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector = 
                setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        DROP TRIGGER IF EXISTS apartments_search_vector_update ON apartments;
        CREATE TRIGGER apartments_search_vector_update
        BEFORE INSERT OR UPDATE OF title, description
        ON apartments
        FOR EACH ROW
        EXECUTE FUNCTION apartments_search_vector_update();
        """)
        
        # Update existing records to populate search vector
        cursor.execute("""
        UPDATE apartments SET 
        search_vector = setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
                        setweight(to_tsvector('english', COALESCE(description, '')), 'B');
        """)
        
        pg_conn.commit()
        logger.info("PostgreSQL triggers created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating PostgreSQL triggers: {e}")
        pg_conn.rollback()
        return False

def run_migration():
    """Run the complete migration process"""
    logger.info("Starting migration from MySQL to PostgreSQL")
    
    # Setup PostgreSQL database
    if not setup_postgres_db():
        logger.error("Failed to setup PostgreSQL database. Migration aborted.")
        return False
    
    # Get DB connections
    mysql_session, mysql_engine = get_mysql_connection()
    pg_conn = get_postgres_connection()
    
    if not mysql_session or not mysql_engine or not pg_conn:
        logger.error("Failed to connect to databases. Migration aborted.")
        return False
    
    try:
        # Create tables in PostgreSQL if they don't exist
        # Create PostgreSQL engine
        pg_engine = create_engine(POSTGRES_DATABASE_URL)
        
        # Create tables
        Base.metadata.create_all(bind=pg_engine)
        logger.info("PostgreSQL tables created")
        
        # Migrate data
        user_count = migrate_users(mysql_session, pg_conn)
        location_count = migrate_locations(mysql_session, pg_conn)
        apartment_count = migrate_apartments(mysql_session, pg_conn)
        
        # Create PostgreSQL triggers
        create_postgres_triggers(pg_conn)
        
        logger.info(f"Migration completed successfully: {user_count} users, {location_count} locations, {apartment_count} apartments")
        
        return True
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
    finally:
        # Close connections
        if mysql_session:
            mysql_session.close()
        if pg_conn:
            pg_conn.close()

if __name__ == "__main__":
    run_migration() 