# src/core/db.py
from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager
from .settings import settings

engine = create_engine(
    str(settings.DATABASE_URL),
    future=True,
    echo=False,
    pool_pre_ping=True,
)

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
