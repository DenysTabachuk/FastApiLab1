from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), index=True)  
    email = Column(String(100)) 
    password = Column(String(100))


class Apartment(Base):
    __tablename__ = 'apartments'

    id = Column(Integer, primary_key=True, index=True)  # Вказано первинний ключ
    name = Column(String(100))
    location = Column(String(100))
    price = Column(Integer)
