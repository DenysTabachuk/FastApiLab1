from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str

class User(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: str

class Token(BaseModel):
    access_token: str
    token_type: str


class ApartmentCreate(BaseModel):
    title: str
    description: str
    price: float
    location: str
    owner_id: int

class ApartmentUpdate(BaseModel):
    title: str
    description: str
    price: float
    location: str