from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Annotated
from sqlmodel import SQLModel, Field, Session, select
from sqlalchemy.exc import IntegrityError
from forms import BusForm, UpdateBusForm, TravelQuery
from models import Bus, Travel, engine, CITIES
from datetime import datetime
import pytz

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


app = FastAPI()

@app.get("/buses/")
def get_buses(session: SessionDep, limit: int | None = None) -> list[Bus]:
    if limit:
        buses = session.exec(select(Bus).limit(limit)).all()
    else:
        buses = session.exec(select(Bus)).all()
    return buses

@app.post("/buses/")
def add_bus(form: BusForm, session: SessionDep):
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

@app.get("/cities/")
def get_cities():
    return CITIES

@app.get("/travels/")
def get_travels(session: SessionDep, query: Annotated[TravelQuery, Query()]):
    first_hour = datetime(
        year = query.schedule.year,
        month = query.schedule.month,
        day = query.schedule.day,
        hour = 0,
        minute = 0,
        tzinfo = pytz.timezone('Europe/Madrid'),
        )
    next_day = datetime(
        year = query.schedule.year,
        month = query.schedule.month,
        day = query.schedule.day + 1,
        hour = 0,
        minute = 0,
        tzinfo = pytz.timezone('Europe/Madrid'),
    )

    travels = session.exec(select(Travel)
        .where(Travel.schedule > first_hour, Travel.schedule < next_day)     
        .where(Travel.origin == query.origin)
        .where(Travel.destination == query.destination)).all()

    if not travels:
        return HTTPException(status_code=404, detail="Travels not found")

    return travels
