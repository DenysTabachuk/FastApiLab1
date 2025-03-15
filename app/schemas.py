from pydantic import BaseModel, Field, validator

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