from fastapi import APIRouter
from .v1 import greeting_route

api_router = APIRouter()
api_router.include_router(greeting_route.router, prefix="", tags="greeting")