from sqlalchemy import create_engine 
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from app.config import POSTGRES_DB_URL
import logging 

logger = logging.getLogger(__name__) 

# 1. Create the SQLAlchemy Engine
# pool_recycle helps prevent connection timeouts in Celery workers
engine = create_engine(
    POSTGRES_DB_URL,
    pool_pre_ping = True, 
    pool_recycle=3600
) 

# 2. Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 

# 3. Create a Base class for declarative models
Base = declarative_base() 

# Dependecy for FastAPI
def get_db():
    db = SessionLocal() 
    try: 
        yield db 
    finally:
        db.close()



# Context manager for Celery tasks and other places where a short-lived session is needed
@contextmanager 
def get_db_session_cm():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()

                       