from pydantic import BaseModel, EmailStr, model_validator
from pydantic import Field as PydanticField
from sqlmodel import SQLModel, Field, Relationship
from sqlmodel import Column, DateTime, BigInteger, String, ForeignKey, SmallInteger
from typing_extensions import Self
from enum import Enum
from datetime import datetime, date
from settings import engine
import pytz


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
    system_information = "system information"
    travels = "travels"
    user = "user account"
    ticket_management = "ticket management"

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
    last_login: datetime = Field(sa_column=Column(DateTime(timezone=True),nullable=True,default=None))
    is_superuser: bool = False
    username: str = Field(sa_column=Column(String(150),unique=True,nullable=False))
    first_name: str | None = Field(max_length=150)
    last_name: str | None = Field(max_length=150)
    email: EmailStr = Field(max_length=254)
    is_staff: bool = False
    is_active: bool = True
    date_joined: datetime = Field(sa_column=Column(
                                                DateTime(timezone=True),
                                                nullable=False,
                                                default=datetime.now(pytz.timezone("Europe/Madrid")),
                                            )
                                        )

class Customer(SQLModel, table=True):
    """
    Application specific user table that has a one to one relation with the default user
    table. It stores information of the users relevant to the application such as their birth_date.
    """
    __tablename__ = 'booking_customer'
    id: int | None = Field(sa_column=Column(BigInteger,primary_key=True),default=None)
    birth_date: date | None = None
    has_large_family: bool = False
    has_reduced_mobility: bool = False
    user_id: int = Field(foreign_key='auth_user.id',unique=True)

class UserBase(SQLModel):
    username: str = Field(max_length=150)
    email: EmailStr = Field(max_length=254)

class PasswordMatch(SQLModel):
    not_hashed_password: str = Field(max_length=128)
    not_hashed_password_repeat: str = Field(max_length=128)

    @model_validator(mode='after')
    def validate_password_is_strong(self) -> Self:
        weak_password_message = """
        Weak password. It must contain at least 8 characters
        using letters and numbers. 
        """
        password = self.not_hashed_password
        if len(password) < 8:
            raise ValueError(weak_password_message)
        weak = {
            "has_letter": False,
            "has_digit": False,
        }
        for character in password:
            if character.islower() or character.isupper():
                weak["has_letter"] = True
                break
        for character in password:
            if character.isdigit():
                weak["has_digit"] = True
                break
        if weak["has_letter"] and weak["has_digit"]:
            return self
        else:
            raise ValidationError(weak_password_message)

    @model_validator(mode='after')
    def validate_password_match(self) -> Self:
        if self.not_hashed_password != self.not_hashed_password_repeat:
            raise ValueError(
                "Passwords do not match."
            )
        return self

class UserPublic(UserBase):
    """
    Users personal information.
    """
    first_name: str | None
    last_name: str | None
    birth_date: date | None
    has_large_family: bool
    has_reduced_mobility: bool

class UserCreate(UserBase, PasswordMatch):
    """
    Information necessary to create a new user and its complementary customer entry.
    """
    first_name: str | None = Field(max_length=150,default=None)
    last_name: str | None = Field(max_length=150,default=None)
    birth_date: date | None = None
    has_large_family: bool = False
    has_reduced_mobility: bool = False

class PasswordChange(PasswordMatch):
    old_password: str = Field(max_length=128)

class UserUpdate(UserBase):
    username: str | None = Field(max_length=150,default=None)
    email: EmailStr | None = Field(max_length=254,default=None)
    first_name: str | None = Field(max_length=150,default=None)
    last_name: str | None = Field(max_length=150,default=None)
    birth_date: date | None = None
    has_large_family: bool | None = None
    has_reduced_mobility: bool | None = None

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
    origin: CityChoices | None = None
    destination: CityChoices | None  = None
    date: date
    to_date: date | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class TicketBase(SQLModel):
    id: int
    seat_number: int
    price: int

class Ticket(TicketBase, table=True):
    __tablename__ = 'booking_ticket'
    id: int | None = Field(sa_column=Column(BigInteger,primary_key=True),default=None)
    seat_number: int = Field(sa_column=Column(SmallInteger,nullable=False))
    price: int | None
    purchase_datetime: datetime = Field(sa_column=Column(DateTime(timezone=True),nullable=False))
    travel_id: int = Field(sa_column=Column(BigInteger,ForeignKey('booking_travel.id'),nullable=False))
    user_id: int = Field(foreign_key='auth_user.id')

class TicketPublic(TicketBase):
    origin: str
    destination: str
    schedule: datetime


# Create the tables in the database running *python3 models.py*.

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
