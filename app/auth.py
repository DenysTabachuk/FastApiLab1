from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from .config import SECRET_KEY, ALGORITHM
from .models import User
from .database import get_db

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str, db: Session ):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")

        if not user_email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Використання db як Session для виконання запиту
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise credentials_exception

    return user
