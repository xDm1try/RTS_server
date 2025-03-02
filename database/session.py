from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.core.settings import settings

engine = create_engine(settings.POSTGRES_URL)
Session = sessionmaker(autoflush=False, autocommit=False, bind=engine)


def get_database() -> Generator:
    try:
        db = Session()
        yield db
    finally:
        db.close()