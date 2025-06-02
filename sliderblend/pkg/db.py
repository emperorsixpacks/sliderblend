from typing import Generator

from sqlmodel import Session, create_engine

from sliderblend.pkg.settings import DatabaseSettings

database = DatabaseSettings()
engine = create_engine(
    database.return_connction_string())  # echo=True logs SQL statements


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
