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

class ClusterUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    auth_user: Optional[str] = None
    auth_token: Optional[str] = None
    auth_type: Optional[str] = None
    verify_ssl: Optional[bool] = None
    is_active: Optional[bool] = None

class ClusterResponse(ClusterBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
