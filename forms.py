from pydantic import BaseModel, Field, model_validator
from typing import Annotated
from typing_extensions import Self

class BusForm(BaseModel):
    bus_id: str = Field(pattern=r'[A-Z]{2}[0-9]{2}',max_length=4)
    seats : int = Field(ge=8,le=72)
    seats_first_row : int = Field(ge=1,le=4)
    seats_reduced_mobility : int = Field(default=0,ge=0,le=2)

    @model_validator(mode='after')
    def validate_seats_fill_all_space(self) -> Self:
        "This function ensures that the last row of the bus is filled."
        if (self.seats - self.seats_first_row) % 4 != 0:
            raise ValueError(
                "The number of seats must be a multiple of 4 after subtracting the first row."
            )
        return self