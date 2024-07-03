from fastapi import FastAPI, APIRouter
from Admin_panel.admin import stuff_router
from auth.auth import register_router
from mobile.mobile import mobile_router

app = FastAPI()
router = APIRouter()


app.include_router(stuff_router)
app.include_router(router)
app.include_router(register_router)
app.include_router(mobile_router)