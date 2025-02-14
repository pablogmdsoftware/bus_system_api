from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Annotated
from sqlmodel import SQLModel, Field, Session, select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import pytz
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from forms import BusForm, UpdateBusForm, TravelQuery, Token, TokenData
from models import Bus, Travel, User, Customer
from models import engine, CITIES

SECRET_KEY = "5134ab42837ae88773721ae43e200d313c5cf6a89fe4f89f85f2e5230cd3f62b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

pw_context = CryptContext(schemes=["django_pbkdf2_sha256"],deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(pytz.timezone("Europe/Madrid")) + expires_delta
    else:
        expire = datetime.now(pytz.timezone("Europe/Madrid")) + timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(session, username, password):
    user = session.exec(select(User).where(User.username==username)).first()
    if not user:
        raise HTTPException(status_code=400,detail="Incorrect username or password")
    if not pw_context.verify(password,user.password):
        raise HTTPException(status_code=400,detail="Incorrect username or password")
    return user

async def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception1 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials1",
        headers={"WWW-Authenticate": "Bearer"},
    )
    credentials_exception2 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials2",
        headers={"WWW-Authenticate": "Bearer"},
    )
    credentials_exception3 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials3",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception1
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception2
    user = session.exec(select(User).where(User.username==token_data.username)).first()
    if user is None:
        raise credentials_exception3    
    return user


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

@app.post("/token/")
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


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user