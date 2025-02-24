from sqlmodel import create_engine

SECRET_KEY = "5134ab42837ae88773721ae43e200d313c5cf6a89fe4f89f85f2e5230cd3f62b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

DB_NAME = "bus_system"
DB_USER = "workuser"
DB_PASSWORD = "qwer1234"
DB_PORT = "5432"

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}")