from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from sqlmodel import Session, select
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta
import pytz

from models import User
from forms import TokenData
from settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from settings import engine


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

pw_context = CryptContext(schemes=["django_pbkdf2_sha256"],deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate_user(session, username, password):
    user = session.exec(select(User).where(User.username==username)).first()
    if not user:
        raise HTTPException(status_code=400,detail="Incorrect username or password")
    if not pw_context.verify(password,user.password):
        raise HTTPException(status_code=400,detail="Incorrect username or password")
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(pytz.timezone("Europe/Madrid")) + expires_delta
    else:
        expire = datetime.now(pytz.timezone("Europe/Madrid")) + timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials1",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = session.exec(select(User).where(User.username==token_data.username)).first()
    if user is None:
        raise credentials_exception    
    return user