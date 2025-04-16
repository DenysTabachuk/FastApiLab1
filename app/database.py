from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

logger.info("Database engine created with SQLAlchemy")

# Create Psycopg connection pool
def get_psycopg_conn():
    """
    Create a direct psycopg2 connection for more advanced PostgreSQL features.
    This connection should be closed after use.
    """
    while True:
        try:
            from .config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_PORT, POSTGRES_DB
            conn = psycopg2.connect(
                host=POSTGRES_SERVER,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                cursor_factory=RealDictCursor
            )
            return conn
        except Exception as error:
            logger.error(f"Error connecting to PostgreSQL database: {error}")
            time.sleep(2)

# SQLAlchemy session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize the database by creating all tables
def init_db():
    try:
        # Import all models here to ensure they are registered with Base.metadata
        from . import models
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create PostgreSQL extensions and functions
        setup_postgres_extensions()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def setup_postgres_extensions():
    """Set up PostgreSQL-specific extensions and functions"""
    try:
        conn = get_psycopg_conn()
        cursor = conn.cursor()
        
        # Enable common extensions
        cursor.execute("""
        CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search
        CREATE EXTENSION IF NOT EXISTS unaccent; -- For accent-insensitive search
        """)
        
        # Create a function to update timestamp on record update
        cursor.execute("""
        CREATE OR REPLACE FUNCTION update_modified_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE 'plpgsql';
        """)
        
        conn.commit()
        logger.info("PostgreSQL extensions and functions set up successfully")
    except Exception as e:
        logger.error(f"Error setting up PostgreSQL extensions: {e}")
    finally:
        if conn:
            conn.close()

# Initialize database on import
init_db()

# Функція для оновлення структури бази даних
def update_database():
    try:
        # Оновлюємо таблицю users
        with engine.connect() as connection:
            # Check if we're using PostgreSQL
            from .config import DATABASE_URL
            if 'postgresql' in DATABASE_URL:
                # PostgreSQL version
                connection.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = 'is_active'
                        ) THEN
                            ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                        END IF;
                        
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = 'created_at'
                        ) THEN
                            ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                        END IF;
                        
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = 'last_login'
                        ) THEN
                            ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
                        END IF;
                        
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'apartments' AND column_name = 'status'
                        ) THEN
                            ALTER TABLE apartments ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
                        END IF;
                        
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'apartments' AND column_name = 'created_at'
                        ) THEN
                            ALTER TABLE apartments ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                        END IF;
                        
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'apartments' AND column_name = 'updated_at'
                        ) THEN
                            ALTER TABLE apartments ADD COLUMN updated_at TIMESTAMP;
                        END IF;
                        
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'apartments' AND column_name = 'moderated_by'
                        ) THEN
                            ALTER TABLE apartments ADD COLUMN moderated_by INTEGER;
                        END IF;
                        
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'apartments' AND column_name = 'moderated_at'
                        ) THEN
                            ALTER TABLE apartments ADD COLUMN moderated_at TIMESTAMP;
                        END IF;
                    END $$;
                """))
            else:
                # MySQL version
                # Перевіряємо чи існує колонка is_active
                result = connection.execute(text("SHOW COLUMNS FROM users LIKE 'is_active'"))
                if not result.fetchone():
                    connection.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                
                # Перевіряємо чи існує колонка created_at
                result = connection.execute(text("SHOW COLUMNS FROM users LIKE 'created_at'"))
                if not result.fetchone():
                    connection.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                
                # Перевіряємо чи існує колонка last_login
                result = connection.execute(text("SHOW COLUMNS FROM users LIKE 'last_login'"))
                if not result.fetchone():
                    connection.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
                
                # Оновлюємо таблицю apartments
                # Перевіряємо чи існує колонка status
                result = connection.execute(text("SHOW COLUMNS FROM apartments LIKE 'status'"))
                if not result.fetchone():
                    connection.execute(text("ALTER TABLE apartments ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
                
                # Перевіряємо чи існує колонка created_at
                result = connection.execute(text("SHOW COLUMNS FROM apartments LIKE 'created_at'"))
                if not result.fetchone():
                    connection.execute(text("ALTER TABLE apartments ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                
                # Перевіряємо чи існує колонка updated_at
                result = connection.execute(text("SHOW COLUMNS FROM apartments LIKE 'updated_at'"))
                if not result.fetchone():
                    connection.execute(text("ALTER TABLE apartments ADD COLUMN updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP"))
                
                # Перевіряємо чи існує колонка moderated_by
                result = connection.execute(text("SHOW COLUMNS FROM apartments LIKE 'moderated_by'"))
                if not result.fetchone():
                    connection.execute(text("ALTER TABLE apartments ADD COLUMN moderated_by INTEGER"))
                
                # Перевіряємо чи існує колонка moderated_at
                result = connection.execute(text("SHOW COLUMNS FROM apartments LIKE 'moderated_at'"))
                if not result.fetchone():
                    connection.execute(text("ALTER TABLE apartments ADD COLUMN moderated_at DATETIME"))
                
            connection.commit()
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")

# Викликаємо оновлення бази даних при запуску
update_database()

