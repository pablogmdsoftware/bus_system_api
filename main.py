from fastapi import FastAPI
from pydantic import BaseModel
from typing import Annotated

from sqlmodel import SQLModel, Field, create_engine, Session

from .forms import Bus


app = FastAPI()

buses = []

@app.get("/buses/")
def get_buses():
    return buses

@app.post("/buses/add/")
def add_bus(bus: Bus):
    buses.append(bus)
    return buses

@app.get("/buses/{bus_id}/")
def get_bus():
    pass

@app.put("/buses/{bus_id}/update/")
def update_bus():
    pass

@app.delete("/buses/{bus_id}/delete/")
def delete_bus():
    pass