from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    """
    Модель для створення нового користувача.
    
    Attributes:
        email (str): Електронна адреса користувача
        password (str): Пароль користувача (мінімум 6 символів)
        first_name (str): Ім'я користувача (мінімум 3 символи)
        last_name (str): Прізвище користувача (мінімум 3 символи)
        phone (str): Номер телефону (10 цифр)
    """
    email: str = Field(..., example="user@example.com", description="Електронна адреса користувача")
    password: str = Field(..., min_length=6, example="securepassword", description="Пароль користувача")
    first_name: str = Field(..., min_length=3, example="John", description="Ім'я користувача")
    last_name: str = Field(..., min_length=3, example="Doe", description="Прізвище користувача")
    phone: str = Field(..., min_length=10, max_length=10, example="1234567890", description="Номер телефону")

    @validator("phone")
    def validate_phone(cls, value):
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        return value

class User(BaseModel):
    """
    Модель користувача для відображення.
    
    Attributes:
        email (str): Електронна адреса користувача
        first_name (str): Ім'я користувача
        last_name (str): Прізвище користувача
        phone (str): Номер телефону
    """
    email: str = Field(..., example="user@example.com", description="Електронна адреса користувача")
    first_name: str = Field(..., min_length=3, example="John", description="Ім'я користувача")
    last_name: str = Field(..., min_length=3, example="Doe", description="Прізвище користувача")
    phone: str = Field(..., min_length=10, max_length=10, example="1234567890", description="Номер телефону")

class LocationCreate(BaseModel):
    """
    Модель для створення локації.
    
    Attributes:
        city (str): Місто
        street (str): Вулиця
        house_number (str): Номер будинку
    """
    city: str = Field(..., min_length=3, example="Kyiv", description="Місто")
    street: str = Field(..., min_length=3, example="Khreshchatyk", description="Вулиця")
    house_number: str = Field(..., min_length=1, example="10", description="Номер будинку")

class ApartmentCreate(BaseModel):
    """
    Модель для створення оголошення про квартиру.
    
    Attributes:
        title (str): Заголовок оголошення
        description (str): Опис квартири
        price (float): Ціна оренди
        location (LocationCreate): Розташування квартири
    """
    title: str = Field(..., min_length=5, example="Cozy Apartment", description="Заголовок оголошення")
    description: str = Field(..., min_length=10, example="A beautiful apartment in the city center", description="Опис квартири")
    price: float = Field(..., ge=0, example=100.0, description="Ціна оренди")
    location: LocationCreate = Field(..., description="Розташування квартири")

class LocationUpdate(BaseModel):
    """
    Модель для оновлення локації.
    
    Attributes:
        city (str): Місто
        street (str): Вулиця
        house_number (str): Номер будинку
    """
    city: str = Field(..., min_length=3, example="Kyiv", description="Місто")
    street: str = Field(..., min_length=3, example="Khreshchatyk", description="Вулиця")
    house_number: str = Field(..., min_length=1, example="10", description="Номер будинку")

class ApartmentUpdate(BaseModel):
    """
    Модель для оновлення оголошення про квартиру.
    
    Attributes:
        title (str): Заголовок оголошення
        description (str): Опис квартири
        price (float): Ціна оренди
        location (LocationUpdate): Розташування квартири
    """
    title: str = Field(..., min_length=5, example="Cozy Apartment", description="Заголовок оголошення")
    description: str = Field(..., min_length=10, example="A beautiful apartment in the city center", description="Опис квартири")
    price: float = Field(..., ge=0, example=100.0, description="Ціна оренди")
    location: LocationUpdate = Field(..., description="Розташування квартири")

class Location(BaseModel):
    """
    Модель локації.
    
    Attributes:
        id (int): Унікальний ідентифікатор
        city (str): Місто
        street (str): Вулиця
        house_number (str): Номер будинку
    """
    id: int = Field(..., example=1, description="Унікальний ідентифікатор")
    city: str = Field(..., min_length=3, example="Kyiv", description="Місто")
    street: str = Field(..., min_length=3, example="Khreshchatyk", description="Вулиця")
    house_number: str = Field(..., min_length=1, example="10", description="Номер будинку")

class Apartment(BaseModel):
    """
    Модель квартири.
    
    Attributes:
        id (int): Унікальний ідентифікатор
        title (str): Заголовок оголошення
        description (str): Опис квартири
        price (float): Ціна оренди
        location (Location): Розташування квартири
        owner_id (int): ID власника
        status (str): Статус оголошення
        created_at (datetime): Дата створення
        updated_at (Optional[datetime]): Дата оновлення
        moderated_by (Optional[int]): ID модератора
        moderated_at (Optional[datetime]): Дата модерації
    """
    id: int = Field(..., example=1, description="Унікальний ідентифікатор")
    title: str = Field(..., min_length=5, example="Cozy Apartment", description="Заголовок оголошення")
    description: str = Field(..., min_length=10, example="A beautiful apartment in the city center", description="Опис квартири")
    price: float = Field(..., ge=0, example=100.0, description="Ціна оренди")
    location: Location = Field(..., description="Розташування квартири")
    owner_id: int = Field(..., example=1, description="ID власника")
    status: str = Field(..., example="pending", description="Статус оголошення")
    created_at: datetime = Field(..., description="Дата створення")
    updated_at: Optional[datetime] = Field(None, description="Дата оновлення")
    moderated_by: Optional[int] = Field(None, example=1, description="ID модератора")
    moderated_at: Optional[datetime] = Field(None, description="Дата модерації")

    class Config:
        from_attributes = True

class UserAdmin(BaseModel):
    """
    Модель користувача для адміністративної панелі.
    
    Attributes:
        id (int): Унікальний ідентифікатор
        email (str): Електронна адреса
        first_name (str): Ім'я
        last_name (str): Прізвище
        phone (str): Номер телефону
        is_admin (bool): Чи є адміністратором
        is_active (bool): Чи активний
        created_at (datetime): Дата створення
        last_login (Optional[datetime]): Дата останнього входу
    """
    id: int = Field(..., example=1, description="Унікальний ідентифікатор")
    email: str = Field(..., example="user@example.com", description="Електронна адреса")
    first_name: str = Field(..., example="John", description="Ім'я")
    last_name: str = Field(..., example="Doe", description="Прізвище")
    phone: str = Field(..., example="1234567890", description="Номер телефону")
    is_admin: bool = Field(..., example=False, description="Чи є адміністратором")
    is_active: bool = Field(..., example=True, description="Чи активний")
    created_at: datetime = Field(..., description="Дата створення")
    last_login: Optional[datetime] = Field(None, description="Дата останнього входу")

    class Config:
        from_attributes = True

class ApartmentAdmin(BaseModel):
    """
    Модель квартири для адміністративної панелі.
    
    Attributes:
        id (int): Унікальний ідентифікатор
        title (str): Заголовок оголошення
        description (str): Опис квартири
        price (int): Ціна оренди
        status (str): Статус оголошення
        created_at (datetime): Дата створення
        updated_at (Optional[datetime]): Дата оновлення
        owner (User): Інформація про власника
        moderated_by (Optional[int]): ID модератора
        moderated_at (Optional[datetime]): Дата модерації
    """
    id: int = Field(..., example=1, description="Унікальний ідентифікатор")
    title: str = Field(..., example="Cozy Apartment", description="Заголовок оголошення")
    description: str = Field(..., example="A beautiful apartment in the city center", description="Опис квартири")
    price: int = Field(..., example=1000, description="Ціна оренди")
    status: str = Field(..., example="pending", description="Статус оголошення")
    created_at: datetime = Field(..., description="Дата створення")
    updated_at: Optional[datetime] = Field(None, description="Дата оновлення")
    owner: User = Field(..., description="Інформація про власника")
    moderated_by: Optional[int] = Field(None, example=1, description="ID модератора")
    moderated_at: Optional[datetime] = Field(None, description="Дата модерації")

class ApartmentModeration(BaseModel):
    """
    Модель для модерації оголошення.
    
    Attributes:
        status (str): Статус модерації
        moderated_by (int): ID модератора
    """
    status: str = Field(..., example="approved", description="Статус модерації")
    moderated_by: int = Field(..., example=1, description="ID модератора")

class SystemStats(BaseModel):
    """
    Модель статистики системи.
    
    Attributes:
        total_users (int): Загальна кількість користувачів
        active_users (int): Кількість активних користувачів
        total_apartments (int): Загальна кількість квартир
        pending_apartments (int): Кількість квартир на модерації
        approved_apartments (int): Кількість одобрених квартир
        rejected_apartments (int): Кількість відхилених квартир
        average_price (float): Середня ціна оренди
        total_owners (int): Кількість власників квартир
    """
    total_users: int = Field(..., example=100, description="Загальна кількість користувачів")
    active_users: int = Field(..., example=80, description="Кількість активних користувачів")
    total_apartments: int = Field(..., example=50, description="Загальна кількість квартир")
    pending_apartments: int = Field(..., example=10, description="Кількість квартир на модерації")
    approved_apartments: int = Field(..., example=35, description="Кількість одобрених квартир")
    rejected_apartments: int = Field(..., example=5, description="Кількість відхилених квартир")
    average_price: float = Field(..., example=1500.0, description="Середня ціна оренди")
    total_owners: int = Field(..., example=30, description="Кількість власників квартир")

class ApartmentObservation(BaseModel):
    """
    Модель для спостереження за квартирами (збереження в закладки).
    
    Attributes:
        id (str): Унікальний ідентифікатор спостереження
        apartment_id (str): ID квартири
        user_id (str): ID користувача
        created_at (datetime): Дата створення спостереження
    """
    id: str = Field(..., example="5f7c7b7c7b7c7b7c7b7c7b7c", description="Унікальний ідентифікатор спостереження")
    apartment_id: str = Field(..., example="5f7c7b7c7b7c7b7c7b7c7b7c", description="ID квартири")
    user_id: str = Field(..., example="5f7c7b7c7b7c7b7c7b7c7b7c", description="ID користувача")
    created_at: datetime = Field(..., description="Дата створення спостереження")
    
    class Config:
        from_attributes = True