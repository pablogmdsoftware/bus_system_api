from sqlmodel import SQLModel, Field, Relationship
from sqlmodel import Column, DateTime, BigInteger, String
from sqlmodel import create_engine
from datetime import datetime, date
from enum import Enum

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
    __tablename__ = 'booking_customer'
    id: int | None = Field(sa_column=Column(BigInteger,primary_key=True),default=None)
    birth_date: date | None
    has_large_family: bool
    has_reduced_mobility: bool
    user_id: int = Field(foreign_key='auth_user.id',unique=True)


engine = create_engine("postgresql://fastapi:qwer1234@localhost:5432/fastapi_test")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
