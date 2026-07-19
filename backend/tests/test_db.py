from sqlalchemy import text
from sqlalchemy.orm import Session


def test_migrations_create_alembic_version_table(db_session: Session) -> None:
    row = db_session.execute(text("SELECT version_num FROM alembic_version")).one()

    assert row.version_num
