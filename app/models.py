from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)

    # Relationships
    owned_apartments = relationship("Apartment", back_populates="owner", foreign_keys="Apartment.owner_id")
    moderated_apartments = relationship("Apartment", back_populates="moderator", foreign_keys="Apartment.moderated_by")

class Apartment(Base):
    __tablename__ = 'apartments'

    id = Column(Integer, primary_key=True, index=True)  
    title = Column(String(100))
    description = Column(String(1000))
    price = Column(Integer)
    owner_id = Column(Integer, ForeignKey('users.id'))  
    location_id = Column(Integer, ForeignKey('locations.id'))
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    moderated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    moderated_at = Column(DateTime, nullable=True)

    # Relationships
    location = relationship("Location", back_populates="apartments")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_apartments")
    moderator = relationship("User", foreign_keys=[moderated_by], back_populates="moderated_apartments")

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100))
    street = Column(String(100))
    house_number = Column(String(10))

    apartments = relationship("Apartment", back_populates="location")