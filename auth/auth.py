import math
import os
import random
import secrets
from typing import List

import aiofiles
import jwt
from datetime import datetime, timedelta

from auth.schemes import Sms_send, Sms_check, Driver_register, Get_regions, Get_districts, Add_car_service, \
    Add_announcement
from auth.utils import generate_token, verify_token
from models.models import Driver, Region, District, Services, Announcement, AnnouncementService, AnnouncementImage, \
    DriverImage
from database import get_async_session
from sqlalchemy import select, insert, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound
from fastapi import Depends, APIRouter, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import redis
import math
import random

# from .utils import generate_token, verify_token

register_router = APIRouter()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Connect to the Redis server
redis_client = redis.Redis(host='localhost', port=6379, db=0)


def generate_code(phone):
    digits = "0123456789"
    OTP = ""
    for i in range(4):
        OTP += digits[math.floor(random.random() * 10)]
    return OTP


def save_code(phone, code, ttl=60):
    key = f"phone:{phone}"
    redis_client.setex(key, ttl, code)


def check_code(phone, code):
    key = f"phone:{phone}"
    stored_code = redis_client.get(key)
    if stored_code is None:
        return False
    return stored_code.decode('utf-8') == code


@register_router.post('/sms-send')
async def send_sms(model: Sms_send):
    phone_number = model.phone
    generated_code = generate_code(phone_number)
    print(generated_code)
    save_code(phone_number, generated_code, 60)
    return {"detail": "SMS sent"}


@register_router.post('/check_sms')
async def check_sms(model: Sms_check, session: AsyncSession = Depends(get_async_session)):
    if not check_code(model.phone, model.code):
        raise HTTPException(status_code=400, detail="Invalid code")

    query = select(Driver).where(Driver.phone == model.phone)
    res = await session.execute(query)
    result = res.scalar_one_or_none()
    if result:
        token = generate_token(result.id)
        return {"token": token}
    else:
        raise HTTPException(status_code=404, detail="Driver not found")


@register_router.post('/register_driver')
async def register_driver(model: Driver_register,
                          file: UploadFile = File(...),
                          session: AsyncSession = Depends(get_async_session)):
    # Insert the driver and flush to get the driver_id
    query = insert(Driver).values(**model.dict(), register_at=datetime.utcnow()).returning(Driver.id)
    result = await session.execute(query)
    driver_id = result.scalar()

    # Save the uploaded file
    url = f'images/{file.filename}'
    async with aiofiles.open(url, 'wb') as zipf:
        content = await file.read()
        await zipf.write(content)
    hashcode = secrets.token_hex(32)
    data = insert(DriverImage).values(url=url,hashcode=hashcode, driver_id=driver_id)
    await session.execute(data)
    await session.commit()
    return {"message": "Registered", "driver_id": driver_id}



# @register_router.post('/add_announcement')
async def add_announcement(model: Add_announcement,
                           file : UploadFile = File(...),
                           token: dict = Depends(verify_token),
                           session: AsyncSession = Depends(get_async_session)):
    if token is None:
        return HTTPException(status_code=401, detail="Unauthorized")

    driver_id = token.get('user_id')
    announcement = Announcement(
        car_id=model.car_id,
        driver_id=driver_id,
        max_price=model.max_price,
        min_price=model.min_price,
        description=model.description,
        added_at=datetime.utcnow(),
        is_active=True
    )
    session.add(announcement)
    await session.flush()
    announcement_id = announcement.id

    announcement_services = [
        AnnouncementService(announcement_id=announcement_id, service_id=service_id)
        for service_id in model.service_id
    ]
    if not os.path.exists('images'):
        os.makedirs('images')

    # Save the uploaded file
    url = f'images/{file.filename}'
    async with aiofiles.open(url, 'wb') as zipf:
        content = await file.read()
        await zipf.write(content)
    hashcode = secrets.token_hex(32)
    data = insert(AnnouncementImage).values(url=url,hashcode=hashcode, announcement_id=announcement_id)
    await session.execute(data)
    await session.commit()

    return {'success': True}


@register_router.get('/get_regions', response_model=List[Get_regions])
async def get_regions(session: AsyncSession = Depends(get_async_session)):
    query = select(Region)
    res = await session.execute(query)
    result = res.scalars().all()
    return result


@register_router.get('/get_districts', response_model=List[Get_districts])
async def get_districts(region_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(District).options(selectinload(District.region)).where(District.region_id == region_id)
    res = await session.execute(query)
    districts = res.scalars().all()

    # Transform the result to match the Pydantic model
    result = [
        Get_districts(
            id=district.id,
            district=district.district,
            region_id=Get_regions(
                id=district.region.id,
                region=district.region.region
            )
        ) for district in districts
    ]

    return result



@register_router.post('/add_car_service')
async def add_car_service(model: Add_car_service, session: AsyncSession = Depends(get_async_session)):
    services_data = [{"name": name, "car_id": model.car_id} for name in model.names]
    query = insert(Services)
    await session.execute(query, services_data)
    await session.commit()

    return {'success': True}
