from datetime import datetime
from bson import ObjectId
from typing import Dict, Any, List, Optional, Union

# Helper to convert MongoDB document ID to str
def convert_object_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB ObjectId to string"""
    if doc and '_id' in doc:
        doc['id'] = str(doc['_id'])
        del doc['_id']
    return doc

# Model schemas as dictionaries to be used with pymongo
# These work as templates for the expected document structure

class User:
    @staticmethod
    def create(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: str,
        is_admin: bool = False
    ) -> Dict[str, Any]:
        """Create a user document"""
        return {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "is_admin": is_admin,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }

    @staticmethod
    def from_db(user_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert user document from database to user model"""
        if not user_doc:
            return None
        return convert_object_id(user_doc)


class Location:
    @staticmethod
    def create(
        city: str,
        street: str,
        house_number: str
    ) -> Dict[str, Any]:
        """Create a location document"""
        return {
            "city": city,
            "street": street,
            "house_number": house_number
        }

    @staticmethod
    def from_db(location_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert location document from database to location model"""
        if not location_doc:
            return None
        return convert_object_id(location_doc)


class Apartment:
    @staticmethod
    def create(
        title: str,
        description: str,
        price: float,
        owner_id: str,
        location: Dict[str, Any],
        status: str = "pending"
    ) -> Dict[str, Any]:
        """Create an apartment document"""
        now = datetime.utcnow()
        return {
            "title": title,
            "description": description,
            "price": price,
            "owner_id": owner_id,
            "location": location,
            "status": status,
            "created_at": now,
            "updated_at": now,
            "moderated_by": None,
            "moderated_at": None
        }

    @staticmethod
    def from_db(apartment_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert apartment document from database to apartment model"""
        if not apartment_doc:
            return None
        
        # Convert the main document ID
        doc = convert_object_id(apartment_doc)
        
        # If location has its own ObjectId, convert that too
        if 'location' in doc and isinstance(doc['location'], dict) and '_id' in doc['location']:
            doc['location'] = convert_object_id(doc['location'])
            
        return doc 