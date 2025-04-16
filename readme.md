# Apartment Rental API with PostgreSQL

This project is a FastAPI application for managing apartment rentals, including user registration, authentication, apartment management, and administration.

## Migration to PostgreSQL

This version has been migrated from MySQL to PostgreSQL to use advanced database features like:

- Full-text search
- JSONB document storage
- Geospatial capabilities
- Advanced statistics with window functions and aggregations

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 13 or higher
- MySQL (source database for migration)

## Installation

1. Clone the repository:
```
git clone <repository-url>
cd FastApiLab1
```

2. Create a virtual environment and activate it:
```
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Linux/Mac
source .venv/bin/activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Configure PostgreSQL:
   - Create a PostgreSQL database
   - Update the connection details in `app/config.py`

## Database Migration

To migrate data from MySQL to PostgreSQL:

1. Make sure both MySQL and PostgreSQL are running
2. Update database connection settings in `app/config.py`
3. Run the migration script:
```
python migrate_to_postgres.py
```

This script will:
- Create the PostgreSQL database if it doesn't exist
- Create all required tables
- Migrate users, locations, and apartments from MySQL to PostgreSQL
- Set up PostgreSQL-specific features like triggers, functions, and indexes

## Running the Application

Start the FastAPI application:

```
uvicorn app.main:app --reload
```

The application will be available at http://localhost:8000

## New PostgreSQL Features

This migration adds several new features:

1. **Full-text Search**: Search apartments by title and description with relevance ranking
2. **JSONB Features**: Store and query flexible apartment features
3. **Geospatial Search**: Find apartments near specific coordinates
4. **Advanced Statistics**: Get detailed statistics using PostgreSQL aggregations
5. **Extended User Activity Reports**: Analyze user activity with window functions

## API Endpoints

New PostgreSQL-specific endpoints:

- `/api/apartments/search` - Full-text search for apartments
- `/api/apartments/nearby` - Find apartments near a location
- `/api/apartments/{apartment_id}/features` - Update apartment features using JSONB
- `/api/apartments/filter-by-features` - Find apartments with specific features
- `/api/locations/{location_id}/coordinates` - Set location coordinates
- `/api/stats/apartments` - Get apartment statistics
- `/api/stats/user-activity` - Get user activity statistics

Admin pages:
- `/admin/statistics/` - View advanced statistics dashboard

## License

MIT
