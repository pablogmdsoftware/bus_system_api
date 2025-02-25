from sqlmodel import create_engine

with open('/etc/api_settings/secret_key.txt') as file:
    SECRET_KEY = file.read().strip()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

DB_NAME = "bus_system"
DB_USER = "workuser"
DB_PASSWORD = "qwer1234"
DB_PORT = "5432"

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}")