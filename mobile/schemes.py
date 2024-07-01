from datetime import datetime
from typing import List
from pydantic import BaseModel

from auth.schemes import Get_regions, Get_districts


class GetCar(BaseModel):
    id: int
    name: str

class GetService(BaseModel):
    id: int
    name: str
    car_id: int


class GetService_by_id(BaseModel):
    id: int
    name: str
    car: GetCar

class Announcement_Service(BaseModel):
    id: int
    announcement_id: int
    service: GetService

class GetDriver(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    region_id: Get_regions
    district_id: Get_districts

class GetAllAnnouncements(BaseModel):
    id: int
    car: GetCar
    driver: GetDriver
    max_price: float
    min_price: float
    description: str
    added_at: datetime
    services: List[Announcement_Service]
