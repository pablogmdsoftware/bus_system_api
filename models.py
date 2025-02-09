from sqlmodel import SQLModel, Field, create_engine


CITIES = {
    "M":"Madrid",
    "B":"Barcelona",
    "TO":"Toledo",
    "BU":"Burgos",
    "SO":"Soria",
    "OV":"Oviedo",
    "PO":"Pontevedra",
}

class Bus(SQLModel, table=True):
    __tablename__ = "booking_bus"
    bus_id: str = Field(primary_key=True)
    seats : int = Field()
    seats_first_row : int = Field()
    seats_reduced_mobility : int = Field()


engine = create_engine("postgresql://fastapi:qwer1234@localhost:5432/fastapi_test")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
