from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Annotated
from sqlmodel import SQLModel, Field, Session, select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import pytz
from passlib.context import CryptContext

from models import BusForm, UpdateBusForm, TravelQuery, Token, TokenData
from models import Bus, Travel, User, Customer
from models import UserPublic, UserCreate
from models import CITIES, EndpointTags
from dependencies import SessionDep, authenticate_user, create_access_token, get_current_user
from dependencies import ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI()

@app.get("/buses", tags=[EndpointTags.system_information])
def get_buses(session: SessionDep, limit: int | None = None) -> list[Bus]:
    if limit:
        buses = session.exec(select(Bus).limit(limit)).all()
    else:
        buses = session.exec(select(Bus)).all()
    return buses

@app.get("/buses/{bus_id}", tags=[EndpointTags.system_information])
def get_bus(bus_id: str, session: SessionDep) -> Bus:
    bus = session.get(Bus, bus_id)
    if not bus:
        return HTTPException(status_code=404, detail="Bus not found")
    return bus

@app.get("/cities", tags=[EndpointTags.system_information])
def get_cities():
    return CITIES

# @app.post("/buses")
# def add_bus(form: BusForm, session: SessionDep):
#     bus = Bus(
#         bus_id = form.bus_id,
#         seats = form.seats,
#         seats_first_row = form.seats_first_row,
#         seats_reduced_mobility = form.seats_reduced_mobility,
#     )
#     try:
#         session.add(bus)
#         session.commit()
#         session.refresh(bus)
#     except IntegrityError:
#         raise HTTPException(
#             status_code=400,
#             detail=f"The bus id {form.bus_id} is already in the database",
#         )
#     return bus

# @app.put("/buses/{bus_id}")
# def update_bus(bus_id: str, form: UpdateBusForm, session: SessionDep):
#     bus = session.get(Bus, bus_id)
#     if not bus:
#         return HTTPException(status_code=404, detail="Bus not found")
#     bus.seats = form.seats
#     bus.seats_first_row  = form.seats_first_row
#     bus.seats_reduced_mobility = form.seats_reduced_mobility
#     session.add(bus)
#     session.commit()
#     session.refresh(bus)
#     return bus

# @app.delete("/buses/{bus_id}")
# def delete_bus(bus_id: str, session: SessionDep):
#     bus = session.get(Bus, bus_id)
#     if not bus:
#         return HTTPException(status_code=404, detail="Bus not found")
#     session.delete(bus)
#     session.commit()
#     return {"ok": True}

@app.get("/travels", tags=[EndpointTags.travels])
def get_travels(session: SessionDep, query: Annotated[TravelQuery, Query()]):
    """
    Get the travels scheduled. Travels within a date range can be retrived 
    setting to_date as the second date.
    """
    first_hour = datetime(
        year = query.date.year,
        month = query.date.month,
        day = query.date.day,
        hour = 0,
        minute = 0,
        tzinfo = pytz.timezone('Europe/Madrid'),
    )
    if not query.to_date:
        query.to_date = query.date
    next_day = datetime(
        year = query.to_date.year,
        month = query.to_date.month,
        day = query.to_date.day + 1,
        hour = 0,
        minute = 0,
        tzinfo = pytz.timezone('Europe/Madrid'),
    )

    if query.origin and query.destination:
        travels = session.exec(select(Travel)
            .where(Travel.schedule > first_hour, Travel.schedule < next_day)     
            .where(Travel.origin == query.origin)
            .where(Travel.destination == query.destination)).all()
    elif query.origin and not query.destination:
        travels = session.exec(select(Travel)
            .where(Travel.schedule > first_hour, Travel.schedule < next_day)     
            .where(Travel.origin == query.origin)).all()
    elif query.destination and not query.origin:
        travels = session.exec(select(Travel)
            .where(Travel.schedule > first_hour, Travel.schedule < next_day)     
            .where(Travel.destination == query.destination)).all()
    else:
        travels = session.exec(select(Travel)
            .where(Travel.schedule > first_hour, Travel.schedule < next_day)).all()     

    if not travels:
        raise HTTPException(status_code=204, detail="Travels not found")

    return travels

@app.post("/users", tags=[EndpointTags.user])
def add_user(session: SessionDep, user_create: UserCreate) -> UserPublic:
    pw_context = CryptContext(schemes=["django_pbkdf2_sha256"],deprecated="auto")
    password = pw_context.hash(user_create.not_hashed_password)
    user = User(
        password = password,
        username = user_create.username,
        email = user_create.email,
        first_name = user_create.first_name,
        last_name = user_create.last_name,
    )
    try:    
        session.add(user)
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="That username is already taken, please choose another."
        )
    session.refresh(user)

    customer = Customer(
        birth_date = user_create.birth_date,
        has_large_family = user_create.has_large_family,
        has_reduced_mobility = user_create.has_reduced_mobility,
        user_id = user.id,
    )
    session.add(customer)
    session.commit()

    user_public = UserPublic(
        id = user.id,
        username = user.username,
        email = user.email,
        first_name = user.first_name,
        last_name = user.last_name,
        birth_date = customer.birth_date,
        has_large_family = customer.has_large_family,
        has_reduced_mobility = customer.has_reduced_mobility,
    )

    return user_public

@app.get("/users/me",tags=[EndpointTags.user], response_model=User)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user

@app.patch("/users/me", tags=[EndpointTags.user])
def update_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    pass

@app.delete("/users/me", tags=[EndpointTags.user])
def delete_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    pass

@app.get("/users/me/tickets", tags=[EndpointTags.ticket_management])
def get_tickets(current_user: Annotated[User, Depends(get_current_user)]):
    pass

@app.post("/users/me/tickets", tags=[EndpointTags.ticket_management])
def add_ticket(current_user: Annotated[User, Depends(get_current_user)]):
    pass

@app.get("/users/me/tickets/{ticket_id}", tags=[EndpointTags.ticket_management])
def get_ticket(ticket_id: int, current_user: Annotated[User, Depends(get_current_user)]):
    pass

@app.delete("/users/me/tickets/{ticket_id}", tags=[EndpointTags.ticket_management])
def delete_ticket_with_future_date(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    pass

@app.post("/token")
async def login_for_access_token(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(session,form_data.username,form_data.password)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub":user.username},
        expires_delta = access_token_expires,
    )
    return Token(access_token=access_token,token_type="Bearer")