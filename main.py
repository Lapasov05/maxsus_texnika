from typing import List

from fastapi import FastAPI, Depends, HTTPException, APIRouter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update

from database import get_async_session
from auth.auth import register_router
from mobile.mobile import mobile_router

app = FastAPI()
router = APIRouter()


app.include_router(router)
app.include_router(register_router)
app.include_router(mobile_router)