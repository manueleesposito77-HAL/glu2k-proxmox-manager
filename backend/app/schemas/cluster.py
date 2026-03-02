from pydantic import BaseModel
from typing import Optional

class ClusterBase(BaseModel):
    name: str
    host: str
    port: int = 8006
    auth_user: str
    auth_type: str = "token"
    verify_ssl: bool = False

class ClusterCreate(ClusterBase):
    auth_token: str

class ClusterResponse(ClusterBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
