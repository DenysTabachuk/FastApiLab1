from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100)) 
    password = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(10))


class Apartment(Base):
    __tablename__ = 'apartments'

    id = Column(Integer, primary_key=True, index=True)  
    title = Column(String(100))
    location = Column(String(100))
    description = Column(String(1000))
    price = Column(Integer)
    owner_id = Column(Integer, ForeignKey('users.id'))  