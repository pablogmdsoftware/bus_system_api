from sqlmodel import create_engine

SECRET_KEY = "5134ab42837ae88773721ae43e200d313c5cf6a89fe4f89f85f2e5230cd3f62b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

engine = create_engine("postgresql://workuser:qwer1234@localhost:5432/fastapi_test")