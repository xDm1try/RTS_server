from fastapi import APIRouter
from fastapi import Depends
from starlette import status


router = APIRouter()


@router.get("/announce_response", status_code=status.HTTP_200_OK)
def get_main_page():
    return {"Message": "Hello"}
