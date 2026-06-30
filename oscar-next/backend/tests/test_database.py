"""
Phase 0.2 — SQLAlchemy + MariaDB connection tests.
Requires a live Oscar MariaDB on localhost:3306.
Run: uv run pytest tests/test_database.py -v
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.config import get_settings

settings = get_settings()


@pytest.fixture
async def db_session():
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def test_db_connects(db_session):
    result = await db_session.execute(text("SELECT 1 AS alive"))
    row = result.fetchone()
    assert row[0] == 1


async def test_core_oscar_tables_exist(db_session):
    result = await db_session.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name IN (
            'demographic', 'appointment', 'provider',
            'casemgmt_note', 'prescription', 'log',
            'security', 'secRole', 'allergies', 'preventions'
        )
        ORDER BY table_name
    """))
    found = {row[0] for row in result.fetchall()}
    expected = {
        'demographic', 'appointment', 'provider',
        'casemgmt_note', 'prescription', 'log',
        'security', 'secRole', 'allergies', 'preventions'
    }
    missing = expected - found
    assert not missing, f"Missing Oscar tables: {missing}"


async def test_demographic_table_readable(db_session):
    result = await db_session.execute(text("""
        SELECT demographic_no, first_name, last_name, date_of_birth, sex, patient_status
        FROM demographic
        LIMIT 3
    """))
    rows = result.fetchall()
    assert len(rows) >= 0  # may be 0 in a fresh DB — just confirm no error
    for row in rows:
        assert row[0] is not None  # demographic_no must exist


async def test_provider_table_readable(db_session):
    result = await db_session.execute(text("""
        SELECT provider_no, first_name, last_name, provider_type
        FROM provider
        LIMIT 3
    """))
    rows = result.fetchall()
    assert len(rows) >= 0


async def test_appointment_table_readable(db_session):
    result = await db_session.execute(text("""
        SELECT appointment_no, demographic_no, provider_no,
               appointment_date, start_time, status
        FROM appointment
        LIMIT 3
    """))
    rows = result.fetchall()
    assert len(rows) >= 0


async def test_audit_log_table_writable(db_session):
    """Verify audit log writes work — this is the PHIPA compliance gate.
    Oscar 'log' table schema: id, dateTime, provider_no, action, content,
    contentId, ip, demographic_no, data, securityId
    """
    await db_session.execute(text("""
        INSERT INTO log
            (dateTime, provider_no, action, content, contentId, ip, data)
        VALUES
            (NOW(), 'oscar-next-setup', 'test',
             'oscar-next Phase 0.2 audit test', 'test-0.2',
             '127.0.0.1', 'Phase 0.2 DB connection verified')
    """))
    await db_session.commit()

    result = await db_session.execute(text("""
        SELECT action, content FROM log
        WHERE content = 'oscar-next Phase 0.2 audit test'
        ORDER BY dateTime DESC
        LIMIT 1
    """))
    row = result.fetchone()
    assert row is not None
    assert row[0] == "test"

    # Clean up
    await db_session.execute(text("""
        DELETE FROM log WHERE content = 'oscar-next Phase 0.2 audit test'
    """))
    await db_session.commit()


async def test_zero_date_handling(db_session):
    """Oscar stores 0000-00-00 for unknown dates — verify we can read without crashing."""
    result = await db_session.execute(text("""
        SELECT demographic_no, date_of_birth
        FROM demographic
        WHERE date_of_birth = '0000-00-00'
        LIMIT 3
    """))
    rows = result.fetchall()
    # Just confirm the query runs — zero dates exist in real Oscar DBs
    assert rows is not None


async def test_security_table_readable(db_session):
    """Verify the auth/RBAC tables are accessible."""
    result = await db_session.execute(text("""
        SELECT user_name, provider_no
        FROM security
        LIMIT 3
    """))
    rows = result.fetchall()
    assert len(rows) >= 0


async def test_sec_role_table_readable(db_session):
    result = await db_session.execute(text("""
        SELECT role_name, description
        FROM secRole
        LIMIT 5
    """))
    rows = result.fetchall()
    assert len(rows) >= 0
