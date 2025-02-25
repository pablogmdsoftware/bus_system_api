from sqlmodel import create_engine

with open('/etc/api_settings/secret_key.txt') as file:
    SECRET_KEY = file.read().strip()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

with open('/etc/api_settings/db_name.txt') as file:
    DB_NAME = file.read().strip()

with open('/etc/api_settings/db_user.txt') as file:
    DB_USER = file.read().strip()

with open('/etc/api_settings/db_password.txt') as file:
    DB_PASSWORD = file.read().strip()

with open('/etc/api_settings/db_port.txt') as file:
    DB_PORT = file.read().strip()

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}")