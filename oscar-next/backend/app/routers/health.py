from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "oscar-next-api"}


@router.get("/health/db")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Verify database connection and that core Oscar tables exist."""
    result = await db.execute(text("SELECT 1"))
    result.fetchone()

    # Verify the core Oscar tables we depend on exist
    tables_check = await db.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name IN (
            'demographic', 'appointment', 'provider',
            'casemgmt_note', 'prescription', 'oscar_log'
        )
        ORDER BY table_name
    """))
    found_tables = [row[0] for row in tables_check.fetchall()]
    expected = {"demographic", "appointment", "provider", "casemgmt_note", "prescription", "oscar_log"}
    missing = expected - set(found_tables)

    return {
        "status": "ok" if not missing else "degraded",
        "database": "connected",
        "oscar_tables_found": found_tables,
        "oscar_tables_missing": list(missing),
    }
