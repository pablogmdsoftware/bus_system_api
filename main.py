from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated
from sqlmodel import SQLModel, Field, create_engine, Session
from sqlalchemy.exc import IntegrityError
from forms import BusForm, UpdateBusForm
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
def get_bus(bus_id: str, session: SessionDep):
    bus = session.get(Bus, bus_id)
    if not bus:
        return HTTPException(status_code=404, detail="Bus not found")
    return bus

@app.put("/buses/{bus_id}/")
def update_bus(bus_id: str, form: UpdateBusForm, session: SessionDep):
    bus = session.get(Bus, bus_id)
    if not bus:
        return HTTPException(status_code=404, detail="Bus not found")
    bus.seats = form.seats
    bus.seats_first_row  = form.seats_first_row
    bus.seats_reduced_mobility = form.seats_reduced_mobility
    session.add(bus)
    session.commit()
    session.refresh(bus)
    return bus

@app.delete("/buses/{bus_id}/")
def delete_bus(bus_id: str, session: SessionDep):
    bus = session.get(Bus, bus_id)
    if not bus:
        return HTTPException(status_code=404, detail="Bus not found")
    session.delete(bus)
    session.commit()
    return {"ok": True}