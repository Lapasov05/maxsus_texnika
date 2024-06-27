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


class Region(Base):
    __tablename__ = 'region'
    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String)

    districts = relationship('District', back_populates='region')
    drivers = relationship('Driver', back_populates='region')


class District(Base):
    __tablename__ = 'district'
    id = Column(Integer, primary_key=True, autoincrement=True)
    district = Column(String)
    region_id = Column(Integer, ForeignKey('region.id'))

    region = relationship('Region', back_populates='districts')
    drivers = relationship('Driver', back_populates='district')


class Driver(Base):
    __tablename__ = 'driver'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    region_id = Column(Integer, ForeignKey('region.id'), nullable=True)
    district_id = Column(Integer, ForeignKey('district.id'), nullable=True)
    register_at = Column(TIMESTAMP, default=datetime.utcnow)

    region = relationship('Region', back_populates='drivers')
    district = relationship('District', back_populates='drivers')
    announcements = relationship('Announcement', back_populates='driver')
    images = relationship('DriverImage', back_populates='driver')


class Cars(Base):
    __tablename__ = 'cars'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    services = relationship('Services', back_populates='car')
    announcements = relationship('Announcement', back_populates='car')


class Services(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    car_id = Column(Integer, ForeignKey('cars.id'))

    car = relationship('Cars', back_populates='services')
    announcement_services = relationship('AnnouncementService', back_populates='service')


class Announcement(Base):
    __tablename__ = 'announcement'
    id = Column(Integer, primary_key=True, autoincrement=True)
    car_id = Column(Integer, ForeignKey('cars.id'))
    driver_id = Column(Integer, ForeignKey('driver.id'))
    max_price = Column(Float)
    min_price = Column(Float)
    description = Column(String)
    added_at = Column(Date, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    @validates('min_price')
    def validate_min_price(self, key, value):
        if value < 10000:
            raise ValueError("min_price should be at least 10000")
        return value

    driver = relationship('Driver', back_populates='announcements')
    car = relationship('Cars', back_populates='announcements')
    announcement_services = relationship('AnnouncementService', back_populates='announcement')
    images = relationship('AnnouncementImage', back_populates='announcement')


class AnnouncementService(Base):
    __tablename__ = 'announcement_service'
    id = Column(Integer, primary_key=True, autoincrement=True)
    announcement_id = Column(Integer, ForeignKey('announcement.id'))
    service_id = Column(Integer, ForeignKey('services.id'))

    announcement = relationship('Announcement', back_populates='announcement_services')
    service = relationship('Services', back_populates='announcement_services')


class DriverImage(Base):
    __tablename__ = 'driver_images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(Integer, ForeignKey('driver.id'))
    url = Column(String)

    driver = relationship('Driver', back_populates='images')


class AnnouncementImage(Base):
    __tablename__ = 'announcement_images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    announcement_id = Column(Integer, ForeignKey('announcement.id'))
    url = Column(Text)

    announcement = relationship('Announcement', back_populates='images')
