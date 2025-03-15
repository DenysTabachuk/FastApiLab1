from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from .config import SECRET_KEY, ALGORITHM
from .models import User
from .database import get_db

def create_access_token(data: dict):
    """Створення токену для доступу"""
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Повертає поточного користувача на основі токену в cookie.
    Якщо користувач не авторизований, повертає None.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if not user_email:
            return None
    except JWTError:
        return None

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return None

    return user

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Повертає поточного авторизованого користувача.
    Якщо користувач не авторизований або токен недійсний — кидає помилку 401.
    """
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")

        if not user_email:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
