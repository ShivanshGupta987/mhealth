"""sql_db.py - Re-exports the shared database infrastructure from app.sql_db.

All models (backend + twilio) use the same Base, engine, and session factory
so that a single Alembic configuration can manage every table.
"""
from app.sql_db import Base, engine, SessionLocal, get_db, get_db_session_cm

__all__ = ["Base", "engine", "SessionLocal", "get_db", "get_db_session_cm"]
