from sqlalchemy.orm import Session
from . import models, schemas


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
    
def create_apartment(db: Session, apartment: schemas.ApartmentCreate):
    db_apartment = models.Apartment(**apartment.dict())
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
    db.query(models.Apartment).filter(models.Apartment.id == apartment_id).update(apartment.dict())
    db.commit()
    return db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()

def delete_apartment(db: Session, apartment_id: int):
    db.query(models.Apartment).filter(models.Apartment.id == apartment_id).delete()
    db.commit()
    return True