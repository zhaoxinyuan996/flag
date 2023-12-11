from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    id: Optional[int]

    username: Optional[str]
    password: Optional[str]
    phone: Optional[int]

    email: Optional[str]
    wechat_id: Optional[str]
    google_id: Optional[str]
    apple_id: Optional[str]

    signature: Optional[str]
    head_uri: Optional[str]
    background_url: Optional[str]


class SignUp0d1(BaseModel):
    username: Optional[str]
    password: Optional[str]