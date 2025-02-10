from sqlmodel import SQLModel, Field, Relationship
from sqlmodel import Column, DateTime, BigInteger
from sqlmodel import create_engine
from datetime import datetime
from enum import Enum


class CitiesEnum(str, Enum):
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
    
    travels: list["Travel"] = Relationship(back_populates="travel",passive_deletes="all")

class Travel(SQLModel, table=True):
    __tablename__ = 'booking_travel'
    id: int | None = Field(sa_column=Column(BigInteger,primary_key=True),default=None)
    schedule: datetime = Field(sa_column=Column(DateTime(timezone=True),nullable=False))
    origin: str = Field(max_length=2)
    destination: str = Field(max_length=2)
    bus_id: str = Field(max_length=4,foreign_key='booking_bus.bus_id')


engine = create_engine("postgresql://fastapi:qwer1234@localhost:5432/fastapi_test")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
