from sqlmodel import create_engine

with open('/etc/api_settings/secret_key.txt') as file:
    SECRET_KEY = file.read().strip()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

engine = create_engine("postgresql://workuser:qwer1234@localhost:5432/fastapi_test")