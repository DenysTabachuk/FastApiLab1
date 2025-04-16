# Apartment Rental API with MongoDB

This project is a migration of the original Apartment Rental API from MySQL to MongoDB. The migration maintains all existing functionality while adding new MongoDB-specific features.

## Prerequisites

- Python 3.8+
- MongoDB 4.4+ or MongoDB Atlas account
- Docker and Docker Compose (optional)

## Installation

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Configure MongoDB connection:
   - Edit `app/config.py` to set your MongoDB connection details if needed

## Running MongoDB

### Option 1: Using Docker Compose

```bash
docker-compose up -d mongodb
```

### Option 2: Local MongoDB installation

Make sure MongoDB is installed and running on your system.

## Data Migration

To migrate existing data from MySQL to MongoDB:

1. Ensure that both MySQL and MongoDB are running
2. Run the migration script:
   ```bash
   python run_direct_migration.py
   ```
3. Check the migration log (`

# Start MySQL with Docker
docker-compose up -d mysql

# Create the tables
python -c "from app.models import Base; from sqlalchemy import create_engine; from app.config import DATABASE_URL; engine = create_engine(DATABASE_URL); Base.metadata.create_all(bind=engine)"