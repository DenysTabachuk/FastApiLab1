from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., min_length=6, example="securepassword")
    first_name: str = Field(..., min_length=3, example="John")
    last_name: str = Field(..., min_length=3, example="Doe")
    phone: str = Field(..., min_length=10, max_length=10, example="1234567890")

    @validator("phone")
    def validate_phone(cls, value):
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        return value

class User(BaseModel):
    email: str = Field(..., example="user@example.com")
    first_name: str = Field(..., min_length=3, example="John")
    last_name: str = Field(..., min_length=3, example="Doe")
    phone: str = Field(..., min_length=10, max_length=10, example="1234567890")

class LocationCreate(BaseModel):
    city: str = Field(..., min_length=3, example="Kyiv")
    street: str = Field(..., min_length=3, example="Khreshchatyk")
    house_number: str = Field(..., min_length=1, example="10")

class ApartmentCreate(BaseModel):
    title: str = Field(..., min_length=5, example="Cozy Apartment")
    description: str = Field(..., min_length=10, example="A beautiful apartment in the city center")
    price: float = Field(..., ge=0, example=100.0)
    location: LocationCreate

class LocationUpdate(BaseModel):
    city: str = Field(..., min_length=3, example="Kyiv")
    street: str = Field(..., min_length=3, example="Khreshchatyk")
    house_number: str = Field(..., min_length=1, example="10")

class ApartmentUpdate(BaseModel):
    title: str = Field(..., min_length=5, example="Cozy Apartment")
    description: str = Field(..., min_length=10, example="A beautiful apartment in the city center")
    price: float = Field(..., ge=0, example=100.0)
    location: LocationUpdate

class Location(BaseModel):
    id: int = Field(..., example=1)
    city: str = Field(..., min_length=3, example="Kyiv")
    street: str = Field(..., min_length=3, example="Khreshchatyk")
    house_number: str = Field(..., min_length=1, example="10")

class UserAdmin(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class ApartmentAdmin(BaseModel):
    id: int
    title: str
    description: str
    price: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner: User
    moderated_by: Optional[int] = None
    moderated_at: Optional[datetime] = None

class ApartmentModeration(BaseModel):
    status: str = Field(..., example="approved")
    moderated_by: int

class SystemStats(BaseModel):
    total_users: int
    active_users: int
    total_apartments: int
    pending_apartments: int
    approved_apartments: int
    rejected_apartments: int
    average_price: float
    total_owners: int