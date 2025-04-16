# MySQL connection (existing)
MYSQL_DATABASE_URL = "mysql+mysqlconnector://root:1234@localhost:3306/fastApiDatabase"

# PostgreSQL connection (new)
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "1234"
POSTGRES_SERVER = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "fastapi_apartments"
POSTGRES_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Use PostgreSQL as the active database
DATABASE_URL = POSTGRES_DATABASE_URL

SECRET_KEY = "1234" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
