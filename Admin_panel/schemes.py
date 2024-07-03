from typing import Optional
from pydantic import BaseModel

from auth.schemes import Get_districts, Get_regions


class Register_stuff(BaseModel):
    firstname: str
    lastname: str
    phone: str
    password_1: str
    password_2: str
    role_id: int
    email: str


class Login_stuff(BaseModel):
    phone: str
    password: str


class Get_all_Drivers(BaseModel):
    id: int
    firstname: str
    lastname: str
    phone: str
    region_id: Get_regions
    district_id: Get_districts
