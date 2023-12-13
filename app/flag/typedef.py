from datetime import datetime
from typing import Optional, Tuple
from app.util import Model


class Flag(Model):
    id: Optional[int]
    user_id: Optional[int]
    location: Optional[Tuple[float, float]]
    content: Optional[str]
    is_open: Optional[int]
    create_time: Optional[datetime]
    update_time: Optional[datetime]
    has_picture: Optional[int]


class AddFlag(Flag):
    location: Tuple[float, float]
    content: str
    is_open: int
