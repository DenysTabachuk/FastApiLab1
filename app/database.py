from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
print("Database engine created")

# Check if tables exist before creating them
inspector = inspect(engine)
tables_exist = True
try:
    # Only check a few key tables
    if not inspector.has_table('users') or not inspector.has_table('apartments'):
        tables_exist = False
        
    # Create tables if they don't exist
    if not tables_exist:
        Base.metadata.create_all(bind=engine)
        print("Database tables created")
except Exception as e:
    print(f"Error checking tables: {e}")
    tables_exist = False

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функція для оновлення структури бази даних
def update_database():
    # Skip if tables don't exist
    if not tables_exist:
        print("Skipping database update - tables don't exist yet")
        return
    
    try:
        # Оновлюємо таблицю users
        with engine.connect() as connection:
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
        print(f"Error updating database: {e}")

# Викликаємо оновлення бази даних при запуску, але тільки якщо таблиці існують
if tables_exist:
    update_database()

