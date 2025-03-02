from pydantic import BaseModel


class AnnouncementModel(BaseModel):
    server_ip: str
    server_port: str
    date: str


class AnnouncementResponseModel(BaseModel):
    device_name: str
    device_ip: str
    device_status: str
    
    
class SimpleTask(BaseModel):
    period: int
    led_gap: int
