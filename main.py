from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated
from sqlmodel import SQLModel, Field, create_engine, Session
from sqlalchemy.exc import IntegrityError
from forms import BusForm
from models import Bus, engine


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


app = FastAPI()

@app.get("/buses/")
def get_buses():
    return buses

@app.post("/buses/")
def add_bus(form: BusForm, session: SessionDep) -> Bus:
    bus = Bus(
        bus_id = form.bus_id,
        seats = form.seats,
        seats_first_row = form.seats_first_row,
        seats_reduced_mobility = form.seats_reduced_mobility,
    )
    try:
        session.add(bus)
        session.commit()
        session.refresh(bus)
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"The bus id {form.bus_id} is already in the database",
        )
    return bus

@app.get("/buses/{bus_id}/")
def get_bus():
    pass

@app.put("/buses/{bus_id}/update/")
def update_bus():
    pass

@app.delete("/buses/{bus_id}/delete/")
def delete_bus():
    pass