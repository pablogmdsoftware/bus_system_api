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
from models import Bus, Travel, User, Customer, Ticket, TicketPublic, TicketBase
from models import UserPublic, UserCreate, PasswordChange, UserUpdate
from models import CITIES, EndpointTags
from dependencies import SessionDep, authenticate_user, create_access_token, get_current_user
from dependencies import ACCESS_TOKEN_EXPIRE_MINUTES, pw_context

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

@app.get("/users/me",tags=[EndpointTags.user])
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> UserPublic:
    customer = session.exec(select(Customer).where(Customer.user_id==current_user.id)).first()
    user = UserPublic(
        username = current_user.username,
        email = current_user.email,
        first_name = current_user.first_name,
        last_name = current_user.last_name,
        birth_date = customer.birth_date,
        has_large_family = customer.has_large_family,
        has_reduced_mobility = customer.has_reduced_mobility,
    )
    return user

@app.patch("/users/me", tags=[EndpointTags.user])
def update_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    user: UserUpdate,
) -> UserPublic:
    customer = session.exec(select(Customer).where(Customer.user_id==current_user.id)).first()
    user_data = user.model_dump(exclude_unset=True)
    
    current_user.sqlmodel_update(user_data)
    customer.sqlmodel_update(user_data)

    session.add(current_user)
    session.add(customer)
    session.commit()
    session.refresh(current_user)
    session.refresh(customer)

    user = UserPublic(
        username = current_user.username,
        email = current_user.email,
        first_name = current_user.first_name,
        last_name = current_user.last_name,
        birth_date = customer.birth_date,
        has_large_family = customer.has_large_family,
        has_reduced_mobility = customer.has_reduced_mobility,
    )

    return user

@app.patch("/users/me/change-password", tags=[EndpointTags.user])
def change_password(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    password_obj: PasswordChange,
) -> dict:
    if not pw_context.verify(password_obj.old_password,current_user.password):
        raise ValueError("Old password was not correct.")
    current_user.password = pw_context.hash(password_obj.not_hashed_password)
    session.add(current_user)
    session.commit()
    return {"ok":True}

@app.delete("/users/me", tags=[EndpointTags.user])
def delete_current_user(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    confirmation: bool = False,
) -> dict:
    """
    Delete your current user. As a safety measure, confirmation parameter is set
    false by default.
    """
    if not confirmation:
        raise HTTPException(status_code=400,detail="Set confirmation equals true to delete an user.")
    customer = session.exec(select(Customer).where(Customer.user_id==current_user.id)).first()
    session.delete(customer)
    session.delete(current_user)
    session.commit()
    return {"ok":f"Your account has been deleted successfully."}

@app.get("/users/me/tickets", tags=[EndpointTags.ticket_management])
def get_tickets(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> list[TicketPublic]:
    statement = select(Ticket,Travel).join(Travel).where(Ticket.user_id==current_user.id)
    data = session.exec(statement).all()
    if not data:
        raise HTTPException(status_code=404,detail="You have not purchased any ticket yet.")

    ticket_list = []
    for ticket, travel in data:
        ticket_public = TicketPublic(
            id = ticket.id,
            seat_number = ticket.seat_number,
            price = ticket.price,
            origin = travel.origin,
            destination = travel.destination,
            schedule = travel.schedule,
        )
        ticket_list.append(ticket_public)

    return ticket_list

@app.get(
    "/users/me/tickets/{ticket_id}",
    tags = [EndpointTags.ticket_management],
)
def get_ticket(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    ticket_id: int,
) -> TicketPublic:
    statement = select(Ticket,Travel).join(Travel).where(Ticket.id==ticket_id)
    data = session.exec(statement).first()
    if not data:
        raise HTTPException(status_code=404,detail="Item not found.")

    ticket, travel = data
    if ticket.user_id != current_user.id:
        raise HTTPException(status_code=404,detail="Item not found.")

    ticket_public = TicketPublic(
        id = ticket.id,
        seat_number = ticket.seat_number,
        price = ticket.price,
        origin = travel.origin,
        destination = travel.destination,
        schedule = travel.schedule,
    )
    
    return ticket_public

@app.delete("/users/me/tickets/{ticket_id}", tags=[EndpointTags.ticket_management])
def delete_ticket_with_future_date(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    ticket_id: int,
) -> dict:
    ticket = session.get(Ticket,ticket_id)
    if not ticket:
        raise HTTPException(status_code=404,detail="Item not found")
    if ticket.user_id != current_user.id:
        raise HTTPException(status_code=404,detail="Item not found")

    day = session.get(Travel,ticket.travel_id).schedule
    if day < datetime.now(pytz.timezone("Europe/Madrid")) + timedelta(days=1):
        raise HTTPException(
            status_code=400,
            detail="You can not cancel tickets with less than one day remaining.",
        )

    session.delete(ticket)
    session.commit()

    return {"ok":True}

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