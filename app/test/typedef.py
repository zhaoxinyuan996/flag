from typing import List
from pydantic import BaseModel


class Sub(BaseModel):
    test: int


class Test(BaseModel):
    f1: int
    f2: str
    f3: List[int]
    f4: List[str]
    f5: Sub
