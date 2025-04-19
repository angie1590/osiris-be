from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo correspondiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DOTENV_PATH = f".env.{ENVIRONMENT}"
load_dotenv(DOTENV_PATH)

# Obtener URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el engine asincrónico
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Crear Session factory
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base declarativa para las entidades
Base = declarative_base()

# Dependency para inyección de sesiones
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session