from typing import Tuple
from pydantic import constr

UUID = constr(min_length=36, max_length=36)
LOCATION = Tuple[float, float]
REQ_LOCATION = Tuple[float, float]
