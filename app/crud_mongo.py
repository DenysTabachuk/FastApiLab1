from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from bson import ObjectId
from pydantic import BaseModel

from . import schemas
from .database_mongo import get_collection
from .models_mongo import User, Location, Apartment

# User Operations
def create_user(user: schemas.UserCreate) -> Dict[str, Any]:
    """Create a new user"""
    users_collection = get_collection("users")
    
    # Check if email exists
    if users_collection.find_one({"email": user.email}):
        return None
    
    # Create user document
    user_data = User.create(
        email=user.email,
        password=user.password,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone
    )
    
    # Insert into database
    result = users_collection.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    
    return User.from_db(user_data)

def get_user(email: str) -> Dict[str, Any]:
    """Get user by email"""
    users_collection = get_collection("users")
    user = users_collection.find_one({"email": email})
    return User.from_db(user)

def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """Get user by ID"""
    users_collection = get_collection("users")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    return User.from_db(user)

def update_user_status(user_id: str, is_active: bool) -> Dict[str, Any]:
    """Update user active status"""
    users_collection = get_collection("users")
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": is_active}}
    )
    if result.modified_count:
        return get_user_by_id(user_id)
    return None

def update_user_last_login(user_id: str) -> Dict[str, Any]:
    """Update user's last login timestamp"""
    users_collection = get_collection("users")
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    if result.modified_count:
        return get_user_by_id(user_id)
    return None

def get_all_users() -> List[Dict[str, Any]]:
    """Get all users"""
    users_collection = get_collection("users")
    users = list(users_collection.find())
    return [User.from_db(user) for user in users]

# Location Operations
def create_location(location: schemas.LocationCreate) -> Dict[str, Any]:
    """Create a new location"""
    locations_collection = get_collection("locations")
    
    # Check if location already exists
    existing = get_existing_location(location)
    if existing:
        return existing
    
    # Create location document
    location_data = Location.create(
        city=location.city,
        street=location.street,
        house_number=location.house_number
    )
    
    # Insert into database
    result = locations_collection.insert_one(location_data)
    location_data["_id"] = result.inserted_id
    
    return Location.from_db(location_data)

def get_existing_location(location: schemas.LocationCreate) -> Dict[str, Any]:
    """Get existing location"""
    locations_collection = get_collection("locations")
    location_doc = locations_collection.find_one({
        "city": location.city,
        "street": location.street,
        "house_number": location.house_number
    })
    return Location.from_db(location_doc)

def get_location_by_id(location_id: str) -> Dict[str, Any]:
    """Get location by ID"""
    locations_collection = get_collection("locations")
    location = locations_collection.find_one({"_id": ObjectId(location_id)})
    return Location.from_db(location)

# Apartment Operations
def create_apartment(apartment: schemas.ApartmentCreate, current_user_id: str) -> Dict[str, Any]:
    """Create a new apartment"""
    apartments_collection = get_collection("apartments")
    users_collection = get_collection("users")
    
    # Get user
    user = users_collection.find_one({"_id": ObjectId(current_user_id)})
    
    # Create location
    location_data = create_location(apartment.location)
    
    # Set status based on user role
    status = "approved" if user and user.get("is_admin", False) else "pending"
    
    # Create apartment document
    apartment_data = Apartment.create(
        title=apartment.title,
        description=apartment.description,
        price=float(apartment.price),
        owner_id=current_user_id,
        location=location_data,
        status=status
    )
    
    # Insert into database
    result = apartments_collection.insert_one(apartment_data)
    apartment_data["_id"] = result.inserted_id
    
    return Apartment.from_db(apartment_data)

def get_apartment(apartment_id: str) -> Dict[str, Any]:
    """Get apartment by ID"""
    apartments_collection = get_collection("apartments")
    apartment = apartments_collection.find_one({"_id": ObjectId(apartment_id)})
    return Apartment.from_db(apartment)

def get_user_apartments(user_id: str) -> List[Dict[str, Any]]:
    """Get all apartments owned by a user"""
    apartments_collection = get_collection("apartments")
    apartments = list(apartments_collection.find({"owner_id": user_id}))
    return [Apartment.from_db(apartment) for apartment in apartments]

def get_all_apartments() -> List[Dict[str, Any]]:
    """Get all apartments"""
    apartments_collection = get_collection("apartments")
    apartments = list(apartments_collection.find())
    return [Apartment.from_db(apartment) for apartment in apartments]

def update_apartment(apartment_id: str, apartment: schemas.ApartmentUpdate) -> Dict[str, Any]:
    """Update apartment"""
    apartments_collection = get_collection("apartments")
    
    # Update location
    location_data = create_location(apartment.location)
    
    # Create update data
    update_data = {
        "title": apartment.title,
        "description": apartment.description,
        "price": float(apartment.price),
        "location": location_data,
        "updated_at": datetime.utcnow()
    }
    
    # Update apartment
    result = apartments_collection.update_one(
        {"_id": ObjectId(apartment_id)},
        {"$set": update_data}
    )
    
    if result.modified_count:
        return get_apartment(apartment_id)
    return None

def delete_apartment(apartment_id: str) -> bool:
    """Delete apartment"""
    apartments_collection = get_collection("apartments")
    result = apartments_collection.delete_one({"_id": ObjectId(apartment_id)})
    return result.deleted_count > 0

def get_pending_apartments() -> List[Dict[str, Any]]:
    """Get all pending apartments"""
    apartments_collection = get_collection("apartments")
    apartments = list(apartments_collection.find({"status": "pending"}))
    return [Apartment.from_db(apartment) for apartment in apartments]

def moderate_apartment(apartment_id: str, status: str, moderator_id: str) -> Dict[str, Any]:
    """Moderate apartment"""
    apartments_collection = get_collection("apartments")
    
    # Create update data
    update_data = {
        "status": status,
        "moderated_by": moderator_id,
        "moderated_at": datetime.utcnow()
    }
    
    # Update apartment
    result = apartments_collection.update_one(
        {"_id": ObjectId(apartment_id)},
        {"$set": update_data}
    )
    
    if result.modified_count:
        return get_apartment(apartment_id)
    return None

def get_apartments(skip: int = 0, limit: int = 100, current_user: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Get apartments with filters"""
    apartments_collection = get_collection("apartments")
    users_collection = get_collection("users")
    
    # Build query
    query = {}
    
    if not current_user or not current_user.get("is_admin", False):
        # If user is not admin, show only approved apartments
        query["status"] = "approved"
        
        # If not admin, exclude apartments of blocked users
        active_users = [user["_id"] for user in users_collection.find({"is_active": True})]
        active_user_ids = [str(user_id) for user_id in active_users]
        query["owner_id"] = {"$in": active_user_ids}
    
    # Execute query with pagination
    apartments = list(apartments_collection.find(query).skip(skip).limit(limit))
    return [Apartment.from_db(apartment) for apartment in apartments]

def get_system_stats() -> Dict[str, Any]:
    """Get system statistics"""
    users_collection = get_collection("users")
    apartments_collection = get_collection("apartments")
    
    # Count users
    total_users = users_collection.count_documents({})
    active_users = users_collection.count_documents({"is_active": True})
    
    # Count apartments
    total_apartments = apartments_collection.count_documents({})
    pending_apartments = apartments_collection.count_documents({"status": "pending"})
    approved_apartments = apartments_collection.count_documents({"status": "approved"})
    rejected_apartments = apartments_collection.count_documents({"status": "rejected"})
    
    # Calculate average price
    price_pipeline = [
        {"$match": {"status": "approved"}},
        {"$group": {"_id": None, "average": {"$avg": "$price"}}}
    ]
    price_result = list(apartments_collection.aggregate(price_pipeline))
    average_price = price_result[0]["average"] if price_result else 0
    
    # Count unique owners
    unique_owners = apartments_collection.distinct("owner_id")
    total_owners = len(unique_owners)
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_apartments": total_apartments,
        "pending_apartments": pending_apartments,
        "approved_apartments": approved_apartments,
        "rejected_apartments": rejected_apartments,
        "average_price": float(average_price),
        "total_owners": total_owners
    } 