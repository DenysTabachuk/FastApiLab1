from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB, UUID, TSVECTOR
import uuid


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    # New PostgreSQL specific fields
    profile_data = Column(JSONB, default={})  # Store flexible profile data
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)

    # Relationships
    owned_apartments = relationship("Apartment", back_populates="owner", foreign_keys="Apartment.owner_id", cascade="all, delete-orphan")
    moderated_apartments = relationship("Apartment", back_populates="moderator", foreign_keys="Apartment.moderated_by")

    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_name', 'first_name', 'last_name'),
    )

class Apartment(Base):
    __tablename__ = 'apartments'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(1000))
    price = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id', ondelete='SET NULL'))
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    moderated_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    
    # New PostgreSQL specific fields
    features = Column(JSONB, default={})  # Store apartment features
    search_vector = Column(TSVECTOR)  # For full-text search
    
    # Relationships
    location = relationship("Location", back_populates="apartments")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_apartments")
    moderator = relationship("User", foreign_keys=[moderated_by], back_populates="moderated_apartments")

    __table_args__ = (
        Index('idx_apartment_status', 'status'),
        Index('idx_apartment_price', 'price'),
        Index('idx_apartment_search', 'search_vector', postgresql_using='gin'),
    )

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False)
    street = Column(String(100))
    house_number = Column(String(20))
    
    # New PostgreSQL specific fields
    coordinates = Column(JSONB)  # Store geo coordinates
    
    apartments = relationship("Apartment", back_populates="location")

    __table_args__ = (
        Index('idx_location_city', 'city'),
    )