# Direct Migration from MySQL to MongoDB

This document explains how to directly migrate data from MySQL to MongoDB for the FastAPI application.

## Prerequisites

- MySQL server running and configured with the correct database
- MongoDB server running
- Python environment with all dependencies installed

## Configuration

Both MySQL and MongoDB connection details are configured in `app/config.py`:

```python
# MySQL Configuration
DATABASE_URL = "mysql+mysqlconnector://root:1234@localhost:3306/fastApiDatabase"

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB_NAME = "fastApiMongoDB"
```

Make sure both database servers are running and accessible with these credentials.

## Running the Migration

To run the direct migration from MySQL to MongoDB:

```bash
python run_direct_migration.py
```

This script will:

1. Connect to the MySQL database
2. Connect to the MongoDB database
3. Migrate all users, locations, and apartments from MySQL to MongoDB
4. Create necessary indexes in MongoDB
5. Log the progress and results in `direct_migration.log`

## Migration Process

The migration process handles:

- Deduplication of records
- Maintaining relationships between entities
- Proper conversion of data types
- Creation of MongoDB indexes for performance

## Troubleshooting

If you encounter any issues:

1. Check `direct_migration.log` for detailed error messages
2. Ensure both MySQL and MongoDB are running
3. Verify you have correct permissions to access both databases

## After Migration

Once the migration is complete, you can run the MongoDB version of the application:

```bash
python run_mongo.py
```

This will start the FastAPI application using MongoDB as the backend database. 