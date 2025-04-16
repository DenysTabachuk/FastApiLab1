# Step-by-Step Migration Guide

This guide provides detailed steps to migrate the FastAPI application from MySQL to PostgreSQL.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.8 or higher
- pip package manager

## Step 1: Install Dependencies

```bash
# Activate your virtual environment
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

## Step 2: Start Database Containers

```bash
# Start both MySQL and PostgreSQL containers
docker-compose up -d
```

This will:
- Start MySQL with your existing database
- Start PostgreSQL with necessary extensions

## Step 3: Verify Database Connections

```bash
# Check if MySQL is running
docker ps | grep mysql

# Check if PostgreSQL is running
docker ps | grep postgres
```

Both containers should be running and healthy.

## Step 4: Run Migration Script

```bash
# Run the migration script
python migrate_to_postgres.py
```

This script will:
1. Check if the PostgreSQL database exists, creating it if needed
2. Create all tables in PostgreSQL
3. Transfer data from MySQL to PostgreSQL
4. Set up PostgreSQL-specific features

The migration log will be saved to `migration.log`.

## Step 5: Verify Migration

```bash
# Connect to PostgreSQL and verify data
docker exec -it fastapi_postgres psql -U postgres -d fastapi_apartments

# Inside PostgreSQL, run these queries:
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM apartments;
SELECT COUNT(*) FROM locations;
```

The counts should match your MySQL database.

## Step 6: Update Configuration

The application is already configured to use PostgreSQL in `app/config.py`. 

You can verify this by checking that:
```python
DATABASE_URL = POSTGRES_DATABASE_URL
```

## Step 7: Start the Application

```bash
# Start the FastAPI application
uvicorn app.main:app --reload
```

## Step 8: Test New Features

Test the new PostgreSQL-specific endpoints:

1. Full-text search: `/api/apartments/search?query=modern`
2. Feature filtering: `/api/apartments/filter-by-features` (POST with JSON features)
3. Nearby apartments: `/api/apartments/nearby?lat=50.450&lon=30.523&radius_km=5`
4. Statistics dashboard: `/admin/statistics/` (admin login required)

## Troubleshooting

### Connection Issues

If you encounter connection issues:

```bash
# Check PostgreSQL logs
docker logs fastapi_postgres

# Check MySQL logs
docker logs fastapi_mysql
```

### Migration Failures

If the migration fails:

1. Check the `migration.log` file
2. Verify database credentials in `app/config.py`
3. Try running the migration with smaller batches

### Data Integrity Issues

If you find data integrity issues:

1. Compare counts in both databases
2. Check for Unicode/encoding issues
3. Verify foreign key relationships

## Rollback Procedure

To roll back to MySQL:

1. Update `app/config.py` to use MySQL:
   ```python
   DATABASE_URL = MYSQL_DATABASE_URL
   ```
2. Restart the application 