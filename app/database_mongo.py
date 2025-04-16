from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from .config import MONGO_URI, MONGO_DB_NAME
from datetime import datetime
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a singleton MongoDB client
class MongoConnection:
    _instance = None
    client: MongoClient = None
    db: Database = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoConnection, cls).__new__(cls)
            cls._instance.connect()
        return cls._instance
    
    def connect(self):
        """Connect to MongoDB with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to MongoDB: {MONGO_URI} (attempt {attempt+1}/{max_retries})")
                self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                
                # Test connection
                self.client.admin.command('ping')
                
                self.db = self.client[MONGO_DB_NAME]
                logger.info(f"Successfully connected to MongoDB: {MONGO_URI}")
                
                # Initialize collections
                self.init_collections()
                
                # Create indexes
                try:
                    from .create_indexes import create_indexes
                    create_indexes()
                except Exception as e:
                    logger.error(f"Error creating indexes: {e}")
                    
                logger.info(f"MongoDB collections initialized")
                return
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Maximum connection attempts reached. MongoDB connection failed.")
                    raise e
    
    def init_collections(self):
        """Initialize collections and create indexes"""
        # Users collection
        if "users" not in self.db.list_collection_names():
            self.db.create_collection("users")
            logger.info("Created users collection")
        self.db.users.create_index("email", unique=True)
        
        # Apartments collection
        if "apartments" not in self.db.list_collection_names():
            self.db.create_collection("apartments")
            logger.info("Created apartments collection")
        self.db.apartments.create_index("owner_id")
        
        # Locations collection
        if "locations" not in self.db.list_collection_names():
            self.db.create_collection("locations")
            logger.info("Created locations collection")

# Function to get database instance
def get_mongo_db() -> Database:
    conn = MongoConnection()
    return conn.db

# Function to get collection
def get_collection(collection_name: str) -> Collection:
    db = get_mongo_db()
    return db[collection_name]

# Migration utility function - can be used to migrate data from SQL to MongoDB
def migrate_sql_to_mongo(sql_data, collection_name):
    """
    Migrate data from SQL to MongoDB
    :param sql_data: Data from SQL database (list of dictionaries)
    :param collection_name: Name of the MongoDB collection
    :return: Result of the insert operation
    """
    collection = get_collection(collection_name)
    if isinstance(sql_data, list) and len(sql_data) > 0:
        return collection.insert_many(sql_data)
    elif isinstance(sql_data, dict):
        return collection.insert_one(sql_data)
    return None

# Initialize MongoDB connection on module load
try:
    mongo_conn = MongoConnection()
    logger.info("MongoDB connection initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MongoDB connection: {e}")
    logger.warning("Application will attempt to reconnect when database is accessed") 