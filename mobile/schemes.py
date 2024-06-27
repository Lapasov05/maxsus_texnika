from datetime import datetime
from pydantic import conint
from typing import Optional, List
from typing import Union

from pydantic import BaseModel, Field


class GetCar(BaseModel):
    id:int
    name:str

class GetService(BaseModel):
    id:int
    name:str
    car_id:int
class AnnouncementService(BaseModel):
    id:int
    announcement_id:int
    service_id:List[GetService]

class GetAllAnnouncements(BaseModel):
    id:int
    car_id: GetCar
    max_price: float
    min_price: float
    description: str
    service_id: List[AnnouncementService]