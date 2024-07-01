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
from fastapi.responses import FileResponse

from models.models import Driver, Region, District, Services, Announcement, AnnouncementService, AnnouncementImage, \
    DriverImage
from database import get_async_session
from sqlalchemy import select, insert, and_, update
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
async def register_driver(
        model: Driver_register,
        session: AsyncSession = Depends(get_async_session)
):
    # Insert the driver and flush to get the driver_id
    query = insert(Driver).values(**model.dict(), register_at=datetime.utcnow()).returning(Driver.id)
    result = await session.execute(query)
    driver_id = result.scalar()
    await session.commit()

    # Generate a token for the registered driver
    token = generate_token(driver_id)

    return {"token": token}


@register_router.post('/add_driver_image')
async def add_driver_image(
        image: UploadFile,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    driver_id = token.get('user_id')

    # Check if the driver exists
    driver_result = await session.execute(select(Driver).where(Driver.id == driver_id))
    driver = driver_result.scalars().first()

    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    url = f'images/{image.filename}'

    # Save the uploaded file
    async with aiofiles.open(url, 'wb') as zipf:
        content = await image.read()
        await zipf.write(content)

    hashcode = secrets.token_hex(32)

    # Check if an image already exists for the driver
    image_result = await session.execute(select(DriverImage).where(DriverImage.driver_id == driver_id))
    driver_image = image_result.scalars().first()

    if driver_image:
        # Update the existing image record
        await session.execute(
            update(DriverImage)
            .where(DriverImage.driver_id == driver_id)
            .values(url=url, hashcode=hashcode)
        )
    else:
        # Insert a new image record
        await session.execute(
            insert(DriverImage)
            .values(url=url, hashcode=hashcode, driver_id=driver_id)
        )

    await session.commit()

    return {"message": "Image added or updated"}


@register_router.get('/get_driver_image/')
async def get_driver_image(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    driver_id = token.get('user_id')
    result = await session.execute(select(DriverImage).where(DriverImage.driver_id == driver_id))
    driver_image = result.scalars().first()
    if driver_image is None:
        raise HTTPException(status_code=404, detail="Image not found for the given driver ID")

    file_path = driver_image.url
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


@register_router.post('/add_announcement')
async def add_announcement(
        model: Add_announcement,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

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
    await session.flush()  # Ensure the ID is generated before accessing it
    announcement_id = announcement.id

    announcement_services = [
        AnnouncementService(announcement_id=announcement_id, service_id=service_id)
        for service_id in model.service_id
    ]
    session.add_all(announcement_services)

    await session.commit()

    return {'announcement_id': announcement_id}


@register_router.get('/get_announcement_image/{announcement_id}')
async def get_announcement_image(announcement_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(AnnouncementImage).where(AnnouncementImage.announcement_id == announcement_id))
    announcement_image = result.scalars().first()
    if announcement_image is None:
        raise HTTPException(status_code=404, detail="Image not found for the given announcement ID")

    file_path = announcement_image.url
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


@register_router.post('/add_announcement_image')
async def add_announcement_image(
        file: UploadFile,
        announcement_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    # Check if announcement exists
    announcement = await session.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Save the uploaded file
    url = f'images/{file.filename}'
    async with aiofiles.open(url, 'wb') as zipf:
        content = await file.read()
        await zipf.write(content)
    hashcode = secrets.token_hex(32)
    data = insert(AnnouncementImage).values(url=url, hashcode=hashcode, announcement_id=announcement_id)
    await session.execute(data)
    await session.commit()

    return {"Success": True, "detail": "Image added"}


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
