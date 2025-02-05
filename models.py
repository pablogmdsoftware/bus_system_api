from pydantic import BaseModel
from typing import Annotated

class Bus(BaseModel):
    bus_id: str
    seats : int
    seats_first_row : int
    seats_reduced_mobility : int = 0