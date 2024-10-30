from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

DATABASE_URL = "sqlite:///news_database.db"
database_engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(database_engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database_engine)
DatabaseSession = sessionmaker(bind=database_engine)