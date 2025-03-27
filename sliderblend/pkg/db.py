from sqlmodel import Session, create_engine

from sliderblend.settings import DatabaseSettings

database = DatabaseSettings()
engine = create_engine(
    database.return_connction_string(), echo=True
)  # echo=True logs SQL statements


def get_session() -> Session:
    with Session(engine) as session:
        yield session
