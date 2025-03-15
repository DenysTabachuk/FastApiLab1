from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100)) 
    password = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(10))
    is_admin = Column(Boolean, default=False)

class Apartment(Base):
    __tablename__ = 'apartments'

    id = Column(Integer, primary_key=True, index=True)  
    title = Column(String(100))
    description = Column(String(1000))
    price = Column(Integer)
    owner_id = Column(Integer, ForeignKey('users.id'))  
    location_id = Column(Integer, ForeignKey('locations.id'))

    location = relationship("Location", back_populates="apartments")

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100))
    street = Column(String(100))
    house_number = Column(String(10))

    apartments = relationship("Apartment", back_populates="location")