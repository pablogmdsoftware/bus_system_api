from pydantic import BaseModel, model_validator
from pydantic import Field as PydanticField
from sqlmodel import SQLModel, Field, Relationship
from sqlmodel import Column, DateTime, BigInteger, String, ForeignKey, SmallInteger
from typing_extensions import Self
from enum import Enum
from datetime import datetime, date
from settings import engine


CITIES = {
    "M":"Madrid",
    "B":"Barcelona",
    "TO":"Toledo",
    "BU":"Burgos",
    "SO":"Soria",
    "OV":"Oviedo",
    "PO":"Pontevedra",
}

class CityChoices(str, Enum):
    madrid = "M"
    barcelona = "B"
    toledo = "TO"
    burgos = "BU"
    soria = "SO"
    oviedo = "OV"
    pontevedra = "PO"

class EndpointTags(str, Enum):
    system_information = "system_information"
    travels = "travels"
    users = "users"
    user_account = "user_account"

class Bus(SQLModel, table=True):
    __tablename__ = "booking_bus"
    bus_id: str = Field(max_length=4,primary_key=True)
    seats: int = Field()
    seats_first_row: int = Field()
    seats_reduced_mobility: int = Field()
    
    # travels: list["Travel"] = Relationship(back_populates="travel",passive_deletes="all")

class Travel(SQLModel, table=True):
    __tablename__ = 'booking_travel'
    id: int | None = Field(sa_column=Column(BigInteger,primary_key=True),default=None)
    schedule: datetime = Field(sa_column=Column(DateTime(timezone=True),nullable=False))
    origin: str = Field(max_length=2)
    destination: str = Field(max_length=2)
    bus_id: str = Field(max_length=4,foreign_key='booking_bus.bus_id')


# There are two users tables in order to guarantee compatibility with the Django project
# that manages the database. Django creates by default an user table and let you link to it
# another table to add extra information.

class User(SQLModel, table=True):
    __tablename__ = 'auth_user'
    id: int | None = Field(primary_key=True,default=None)
    password: str = Field(max_length=128)
    last_login: datetime = Field(sa_column=Column(DateTime(timezone=True),nullable=True))
    is_superuser: bool
    username: str = Field(sa_column=Column(String(150),unique=True,nullable=False))
    first_name: str = Field(max_length=150)
    last_name: str = Field(max_length=150)
    email: str = Field(max_length=254)
    is_staff: bool
    is_active: bool
    date_joined: datetime = Field(sa_column=Column(DateTime(timezone=True),nullable=False))

class Customer(SQLModel, table=True):
    """
    Application specific user table that has a one to one relation with the default user
    table. It stores information of the users relevant to the application such as their birth_date.
    """
    __tablename__ = 'booking_customer'
    id: int | None = Field(sa_column=Column(BigInteger,primary_key=True),default=None)
    birth_date: date | None
    has_large_family: bool
    has_reduced_mobility: bool
    user_id: int = Field(foreign_key='auth_user.id',unique=True)

class UserPublic(SQLModel):
    """
    Users personal information.
    """
    username: str
    first_name: str
    last_name: str
    email: str
    birth_date: date
    has_large_family: bool
    has_reduced_mobility: bool

class Ticket(SQLModel, table=True):
    __tablename__ = 'booking_ticket'
    id: int | None = Field(sa_column=Column(BigInteger,primary_key=True),default=None)
    seat_number: int = Field(sa_column=Column(SmallInteger,nullable=False))
    price: int | None
    purchase_datetime: datetime = Field(sa_column=Column(DateTime(timezone=True),nullable=False))
    travel_id: int = Field(sa_column=Column(BigInteger,ForeignKey('booking_travel.id'),nullable=False))
    user_id: int = Field(foreign_key='auth_user.id')

class BusForm(BaseModel):
    bus_id: str = PydanticField(pattern=r'[A-Z]{2}[0-9]{2}',max_length=4)
    seats : int = PydanticField(ge=8,le=72)
    seats_first_row : int = PydanticField(ge=1,le=4)
    seats_reduced_mobility : int = PydanticField(default=0,ge=0,le=2)

    @model_validator(mode='after')
    def validate_seats_fill_all_space(self) -> Self:
        "This function ensures that the last row of the bus is filled."
        if (self.seats - self.seats_first_row) % 4 != 0:
            raise ValueError(
                "The number of seats must be a multiple of 4 after subtracting the first row."
            )
        return self

class UpdateBusForm(BusForm):
    bus_id: None = None

class TravelQuery(BaseModel):
    """
    This model filter queries to search travels in the database. The schedule format
    is ISO 8601 (yyyy-mm-dd).
    """
    origin: CityChoices
    destination: CityChoices
    schedule: date

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
