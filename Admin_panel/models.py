from datetime import datetime

from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    Text,
    MetaData,
    Boolean,
    TIMESTAMP,
    Date, ForeignKey, Float
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError

metadata = MetaData()
Base = declarative_base()


class Role(Base):
    __tablename__ = 'role'
    metadata=metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(25))

    stuff = relationship('Stuff',back_populates='role')

class Stuff(Base):
    __tablename__ = 'stuff'
    metadata=metadata
    id = Column(Integer,primary_key=True,autoincrement=True)
    firstname = Column(String)
    lastname = Column(String)
    phone = Column(String, unique=True)
    password = Column(String)
    role_id = Column(Integer,ForeignKey('role.id'))
    email = Column(Text,unique=True)
    registred_at = Column(TIMESTAMP, default=datetime.utcnow())
    last_login = Column(TIMESTAMP, default=datetime.utcnow())

    role = relationship('Role',back_populates='stuff')
