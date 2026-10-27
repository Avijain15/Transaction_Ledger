from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL
from app.models import Base


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE OR REPLACE FUNCTION reject_transaction_mutation() RETURNS trigger AS $$
                BEGIN
                    RAISE EXCEPTION 'transactions are immutable';
                END;
                $$ LANGUAGE plpgsql;
                """
            )
        )
        connection.execute(text("DROP TRIGGER IF EXISTS transactions_immutable ON transactions"))
        connection.execute(
            text(
                "CREATE TRIGGER transactions_immutable BEFORE UPDATE OR DELETE ON transactions "
                "FOR EACH ROW EXECUTE FUNCTION reject_transaction_mutation()"
            )
        )
