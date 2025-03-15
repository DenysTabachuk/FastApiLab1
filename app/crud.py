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
    
def create_apartment(db: Session, apartment: schemas.ApartmentCreate,  current_user_id: int):
    db_location = create_location(db, apartment.location)

    db_apartment = models.Apartment(
        title=apartment.title,
        description=apartment.description,
        price=apartment.price,
        owner_id=current_user_id,
        location_id= db_location.id 
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

