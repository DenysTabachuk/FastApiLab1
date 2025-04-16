from fastapi import HTTPException
from jose import JWTError, jwt
from .config import SECRET_KEY, ALGORITHM
from .database_mongo import get_collection
from .models_mongo import User
from typing import Dict, Any, Optional

def create_access_token(data: dict) -> str:
    """Create access token for user"""
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_email_from_token(token: str) -> Optional[str]:
    """Extract email from token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        return email
    except JWTError:
        return None

def get_user_from_email(email: str) -> Dict[str, Any]:
    """Get user from email"""
    users_collection = get_collection("users")
    user = users_collection.find_one({"email": email})
    return User.from_db(user)

def get_current_user_from_token(token: str) -> Dict[str, Any]:
    """Get current user from token"""
    email = get_email_from_token(token)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = get_user_from_email(email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user 