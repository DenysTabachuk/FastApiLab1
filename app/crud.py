from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from datetime import datetime


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User( password = user.password, email=user.email, first_name=user.first_name, last_name=user.last_name, phone=user.phone)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()
    
def create_apartment(db: Session, apartment: schemas.ApartmentCreate, current_user_id: int):
    db_location = create_location(db, apartment.location)
    
    # Отримуємо користувача
    user = db.query(models.User).filter(models.User.id == current_user_id).first()
    
    # Встановлюємо статус в залежності від ролі користувача
    status = 'approved' if user and user.is_admin else 'pending'

    db_apartment = models.Apartment(
        title=apartment.title,
        description=apartment.description,
        price=apartment.price,
        owner_id=current_user_id,
        location_id=db_location.id,
        status=status
    )

    db.add(db_apartment)
    db.commit()
    db.refresh(db_apartment)
    return db_apartment


def get_user_apartments(db: Session, user_id: int):
    return db.query(models.Apartment).filter(models.Apartment.owner_id == user_id).all()

def get_apartment(db: Session, apartment_id: int):
    return db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()

def get_all_apartments(db: Session):
    return db.query(models.Apartment).all()

def update_apartment(db: Session, apartment_id: int, apartment: schemas.ApartmentUpdate):
    apartment_data = apartment.dict(exclude_unset=True)

    location_data = apartment_data.pop('location', None)  
    location_db = db.query(models.Location).filter(models.Location.apartments.any(id=apartment_id)).first()

    if location_db and location_data:
        location_db.city = location_data["city"]
        location_db.street = location_data["street"]
        location_db.house_number = location_data["house_number"]
        db.commit()

    db.query(models.Apartment).filter(models.Apartment.id == apartment_id).update(apartment_data)
    db.commit()

    return db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()

def delete_apartment(db: Session, apartment_id: int):
    db.query(models.Apartment).filter(models.Apartment.id == apartment_id).delete()
    db.commit()
    return True

def create_location(db: Session, location: schemas.LocationCreate):
    db_location = models.Location(
        city=location.city,
        street=location.street,
        house_number=location.house_number
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_existing_location(db: Session, location: schemas.LocationCreate):
    return db.query(models.Location).filter(
        models.Location.city == location.city,
        models.Location.street == location.street,
        models.Location.house_number == location.house_number
    ).first()
 

def get_location_by_id(db: Session, location_id: int):
    return db.query(models.Location).filter(models.Location.id == location_id).first()

# Admin functions
def get_all_users(db: Session):
    return db.query(models.User).all()

def update_user_status(db: Session, user_id: int, is_active: bool):
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = is_active
        db.commit()
    return user

def get_pending_apartments(db: Session):
    return db.query(models.Apartment).filter(models.Apartment.status == 'pending').all()

def moderate_apartment(db: Session, apartment_id: int, status: str, moderator_id: int):
    apartment = get_apartment(db, apartment_id)
    if apartment:
        apartment.status = status
        apartment.moderated_by = moderator_id
        apartment.moderated_at = datetime.utcnow()
        db.commit()
    return apartment

def get_system_stats(db: Session):
    total_users = db.query(func.count(models.User.id)).scalar()
    active_users = db.query(func.count(models.User.id)).filter(models.User.is_active == True).scalar()
    total_apartments = db.query(func.count(models.Apartment.id)).scalar()
    pending_apartments = db.query(func.count(models.Apartment.id)).filter(models.Apartment.status == 'pending').scalar()
    approved_apartments = db.query(func.count(models.Apartment.id)).filter(models.Apartment.status == 'approved').scalar()
    rejected_apartments = db.query(func.count(models.Apartment.id)).filter(models.Apartment.status == 'rejected').scalar()
    average_price = db.query(func.avg(models.Apartment.price)).scalar() or 0
    total_owners = db.query(func.count(func.distinct(models.Apartment.owner_id))).scalar()

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

def update_user_last_login(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if user:
        user.last_login = datetime.utcnow()
        db.commit()
    return user

def get_apartments(db: Session, skip: int = 0, limit: int = 100, current_user: models.User = None):
    query = db.query(models.Apartment)
    
    # If user is not admin, show only approved apartments
    if not current_user or not current_user.is_admin:
        query = query.filter(models.Apartment.status == 'approved')
    
    return query.offset(skip).limit(limit).all()

