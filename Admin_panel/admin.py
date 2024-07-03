from datetime import datetime
from http.client import HTTPException
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from Admin_panel.models import Stuff
from Admin_panel.schemes import Get_all_Drivers, Register_stuff, Login_stuff
from Admin_panel.utils import verify_stuff_token, generate_token_stuff, send_mail
from auth.auth import pwd_context
from auth.schemes import Get_regions, Get_districts
from database import get_async_session
from mobile.schemes import GetDriver, GetDriverImage
from models.models import Driver

stuff_router = APIRouter()


@stuff_router.post('/stuff/login/')
async def login(user: Login_stuff, session: AsyncSession = Depends(get_async_session)):
    query_user = select(Stuff).options(selectinload(Stuff.role)).where(
        Stuff.phone == user.phone
    )

    res_user = await session.execute(query_user)
    user_result = res_user.scalar_one_or_none()

    if user_result and pwd_context.verify(user.password, user_result.password):
        token = generate_token_stuff(user_result.id, user_result.role.name)
        return {"status_code": 200, "detail": token}
    else:
        return {"status_code": 401, "detail": "Login Failed"}


@stuff_router.post('/register_stuff')
async def register_stuff(model: Register_stuff, session: AsyncSession = Depends(get_async_session)):
    try:
        if model.password_1 == model.password_2:
            password_hash = pwd_context.hash(model.password_2)
            query = insert(Stuff).values(
                firstname=model.firstname,
                lastname=model.lastname,
                phone=model.phone,
                password=password_hash,
                email=model.email,
                role_id=model.role_id,
                registred_at=datetime.utcnow()
            )
            await session.execute(query)
            await session.commit()
            send_mail(model.email, model.phone, model.password_2)
            return {"status_code": 200, "detail": "Registered!"}
        else:
            return {"status_code": 400, "detail": "Passwords are not the same!"}
    except Exception as e:
        return {"status_code": 400, "detail": str(e)}


@stuff_router.post('/stuff/add_stuff')
async def register_user_student(model: Register_stuff,
                                token: dict = Depends(verify_stuff_token),
                                session: AsyncSession = Depends(get_async_session)
                                ):
    try:
        role_name = token['role_name']
        if role_name.lower() == 'admin':
            if model.password_1 == model.password_2:
                password_hash = pwd_context.hash(model.password_2)
                query = insert(Stuff).values(firstname=model.first_name,
                                             lastname=model.last_name,
                                             phone=model.phone,
                                             password=password_hash,
                                             email=model.email,
                                             role_id=model.role_id,
                                             registred_at=datetime.utcnow())
                await session.execute(query)
                await session.commit()
                send_mail(model.email, model.phone, model.password_2)
                return HTTPException(status_code=200, detail="Registered!")
            else:
                return HTTPException(status_code=400, detail="Passwords are not same!")
    except Exception as e:
        return HTTPException(status_code=400, detail=f"{e}")

@stuff_router.get('/admin/get_all/users', response_model=List[GetDriver])
async def get_all_users(token: dict = Depends(verify_stuff_token),
                        session: AsyncSession = Depends(get_async_session)):
    if not isinstance(token, dict):
        raise HTTPException(status_code=400, detail="Invalid token")

    role_name = token.get('role_name')
    if role_name and role_name.lower() == 'admin':
        query = select(Driver).options(
            selectinload(Driver.driver_images),
            selectinload(Driver.district),
            selectinload(Driver.region)
        )
        res_user = await session.execute(query)
        result_user = res_user.scalars().all()

        def to_get_regions(region):
            return Get_regions(
                id=region.id,
                region=region.region
            )

        def to_get_districts(district):
            return Get_districts(
                id=district.id,
                district=district.district,
                region_id=to_get_regions(district.region)
            )

        def to_get_driver_images(driver_images):
            return [GetDriverImage(
                id=driver_image.id,
                url=driver_image.url,
                hashcode=driver_image.hashcode
            ) for driver_image in driver_images]

        result_list = [
            GetDriver(
                id=driver.id,
                first_name=driver.first_name,  # Note the change here
                last_name=driver.last_name,    # Note the change here
                phone=driver.phone,
                region_id=to_get_regions(driver.region),
                district_id=to_get_districts(driver.district),
                driver_images=to_get_driver_images(driver.driver_images)
            )
            for driver in result_user
        ]

        return result_list
    else:
        raise HTTPException(status_code=403, detail="Not allowed")
