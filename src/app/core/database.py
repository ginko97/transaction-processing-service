from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()

# Define Base here - this is required for models
Base = declarative_base()

engine = create_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
