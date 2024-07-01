import datetime
import secrets
from typing import List

# import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi_pagination import Page, add_pagination, paginate
# from fastapi_pagination.ext.sqlalchemy import paginate

from sqlalchemy import select, insert, or_, and_, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.schemes import Get_regions, Get_districts
from auth.utils import verify_token
from database import get_async_session
from datetime import datetime, timedelta
from sqlalchemy.orm import selectinload
from mobile.schemes import GetAllAnnouncements, GetCar, GetDriver, GetService, Announcement_Service, GetService_by_id, \
    GetDriverImage, GetAnnouncementImage
from models.models import Announcement, AnnouncementService, Cars, Driver, Services

mobile_router = APIRouter()

@mobile_router.get('/get_announcements', response_model=List[GetAllAnnouncements])
async def get_all_announcements(session: AsyncSession = Depends(get_async_session)):
    query = select(Announcement).options(
        selectinload(Announcement.announcement_services).selectinload(AnnouncementService.service),
        selectinload(Announcement.driver).selectinload(Driver.region),
        selectinload(Announcement.driver).selectinload(Driver.district),
        selectinload(Announcement.driver).selectinload(Driver.driver_images),
        selectinload(Announcement.announcement_images),
        selectinload(Announcement.car)
    )
    res = await session.execute(query)
    announcements = res.scalars().all()

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

    def to_get_service(service):
        return GetService(
            id=service.id,
            name=service.name,
            car_id=service.car_id
        )

    def to_announcement_service(announcement_service):
        return Announcement_Service(
            id=announcement_service.id,
            announcement_id=announcement_service.announcement_id,
            service=to_get_service(announcement_service.service)
        )

    def to_get_driver(driver):
        return GetDriver(
            id=driver.id,
            first_name=driver.first_name,
            last_name=driver.last_name,
            phone=driver.phone,
            region_id=to_get_regions(driver.region),
            district_id=to_get_districts(driver.district),
            driver_images=[to_get_driver_image(image) for image in driver.driver_images]
        )

    def to_get_driver_image(driver_image):
        return GetDriverImage(
            id=driver_image.id,
            url=driver_image.url,
            hashcode=driver_image.hashcode
        )

    def to_get_announcement_image(announcement_image):
        return GetAnnouncementImage(
            id=announcement_image.id,
            url=announcement_image.url,
            hashcode=announcement_image.hashcode
        )

    def to_get_car(car):
        return GetCar(
            id=car.id,
            name=car.name
        )

    result = [
        GetAllAnnouncements(
            id=announcement.id,
            car=to_get_car(announcement.car),
            driver=to_get_driver(announcement.driver),
            max_price=announcement.max_price,
            min_price=announcement.min_price,
            description=announcement.description,
            added_at=announcement.added_at,
            services=[to_announcement_service(aservice) for aservice in announcement.announcement_services],
            announcement_images=[to_get_announcement_image(image) for image in announcement.announcement_images]
        )
        for announcement in announcements
    ]

    return result

@mobile_router.get('/get_service_by_car_id', response_model=List[GetService_by_id])
async def get_services_by_id(car_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Services).options(selectinload(Services.car)).where(Services.car_id == car_id)
    res = await session.execute(query)
    services = res.scalars().all()

    services_list = [
        GetService_by_id(
            id=service.id,
            car=GetCar(
                id=service.car.id,
                name=service.car.name
            ),
            name=service.name
        )
        for service in services
    ]
    return services_list


@mobile_router.get('/search-announcements')
async def get_all_announcements(
        query: str,
        session: AsyncSession = Depends(get_async_session)
) -> Page[GetAllAnnouncements]:
    search_query = f'%{query}%'

    query_data = select(Announcement).options(
        selectinload(Announcement.announcement_services).selectinload(AnnouncementService.service),
        selectinload(Announcement.driver).selectinload(Driver.region),
        selectinload(Announcement.driver).selectinload(Driver.district),
        selectinload(Announcement.car)
    ).where(or_(
        Announcement.description.ilike(search_query),
        Cars.services.any(Services.name.ilike(search_query))
    ))

    data = await session.execute(query_data)
    announcements = data.scalars().all()

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

    def to_get_service(service):
        return GetService(
            id=service.id,
            name=service.name,
            car_id=service.car_id
        )

    def to_announcement_service(announcement_service):
        return Announcement_Service(
            id=announcement_service.id,
            announcement_id=announcement_service.announcement_id,
            service=to_get_service(announcement_service.service)
        )

    def to_get_driver(driver):
        return GetDriver(
            id=driver.id,
            first_name=driver.first_name,
            last_name=driver.last_name,
            phone=driver.phone,
            region_id=to_get_regions(driver.region),
            district_id=to_get_districts(driver.district)
        )

    def to_get_car(car):
        return GetCar(
            id=car.id,
            name=car.name
        )

    result = [
        GetAllAnnouncements(
            id=announcement.id,
            car=to_get_car(announcement.car),
            driver=to_get_driver(announcement.driver),
            max_price=announcement.max_price,
            min_price=announcement.min_price,
            description=announcement.description,
            added_at=announcement.added_at,
            services=[to_announcement_service(aservice) for aservice in announcement.announcement_services]
        )
        for announcement in announcements
    ]

    return paginate(result)


add_pagination(mobile_router)





@mobile_router.get('/get_my_active_announcements',response_model=List[GetAllAnnouncements])
async def get_my_active_announcements(token:dict=Depends(verify_token),
                       session:AsyncSession=Depends(get_async_session)):
    driver_id = token.get('user_id')
    query_data = select(Announcement).options(
        selectinload(Announcement.announcement_services).selectinload(AnnouncementService.service),
        selectinload(Announcement.driver).selectinload(Driver.region),
        selectinload(Announcement.driver).selectinload(Driver.district),
        selectinload(Announcement.car)
    ).where(and_(Announcement.driver_id==driver_id,Announcement.is_active==True))
    res = await session.execute(query_data)
    announcements = res.scalars().all()

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

    def to_get_service(service):
        return GetService(
            id=service.id,
            name=service.name,
            car_id=service.car_id
        )

    def to_announcement_service(announcement_service):
        return Announcement_Service(
            id=announcement_service.id,
            announcement_id=announcement_service.announcement_id,
            service=to_get_service(announcement_service.service)
        )

    def to_get_driver(driver):
        return GetDriver(
            id=driver.id,
            first_name=driver.first_name,
            last_name=driver.last_name,
            phone=driver.phone,
            region_id=to_get_regions(driver.region),
            district_id=to_get_districts(driver.district)
        )

    def to_get_car(car):
        return GetCar(
            id=car.id,
            name=car.name
        )

    result = [
        GetAllAnnouncements(
            id=announcement.id,
            car=to_get_car(announcement.car),
            driver=to_get_driver(announcement.driver),
            max_price=announcement.max_price,
            min_price=announcement.min_price,
            description=announcement.description,
            added_at=announcement.added_at,
            services=[to_announcement_service(aservice) for aservice in announcement.announcement_services]
        )
        for announcement in announcements
    ]
    return result


@mobile_router.get('/get_my_non-active_announcements',response_model=List[GetAllAnnouncements])
async def get_my_non_active_announcements(token:dict=Depends(verify_token),
                       session:AsyncSession=Depends(get_async_session)):
    driver_id = token.get('user_id')
    query_data = select(Announcement).options(
        selectinload(Announcement.announcement_services).selectinload(AnnouncementService.service),
        selectinload(Announcement.driver).selectinload(Driver.region),
        selectinload(Announcement.driver).selectinload(Driver.district),
        selectinload(Announcement.car)
    ).where(and_(Announcement.driver_id==driver_id,Announcement.is_active==False))
    res = await session.execute(query_data)
    announcements = res.scalars().all()

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

    def to_get_service(service):
        return GetService(
            id=service.id,
            name=service.name,
            car_id=service.car_id
        )

    def to_announcement_service(announcement_service):
        return Announcement_Service(
            id=announcement_service.id,
            announcement_id=announcement_service.announcement_id,
            service=to_get_service(announcement_service.service)
        )

    def to_get_driver(driver):
        return GetDriver(
            id=driver.id,
            first_name=driver.first_name,
            last_name=driver.last_name,
            phone=driver.phone,
            region_id=to_get_regions(driver.region),
            district_id=to_get_districts(driver.district)
        )

    def to_get_car(car):
        return GetCar(
            id=car.id,
            name=car.name
        )

    result = [
        GetAllAnnouncements(
            id=announcement.id,
            car=to_get_car(announcement.car),
            driver=to_get_driver(announcement.driver),
            max_price=announcement.max_price,
            min_price=announcement.min_price,
            description=announcement.description,
            added_at=announcement.added_at,
            services=[to_announcement_service(aservice) for aservice in announcement.announcement_services]
        )
        for announcement in announcements
    ]
    return result
