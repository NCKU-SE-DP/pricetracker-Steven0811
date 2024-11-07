from src.database import Base
from src.constants import USERS_TABLE_NAME, USER_NEWS_ASSOCIATION_TABLE_NAME, NEWS_ARTICLES_TABLE_NAME, MAX_USERNAME_LENGTH, MAX_PASSWORD_HASH_LENGTH
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship


user_news_association_table = Table(
    USER_NEWS_ASSOCIATION_TABLE_NAME,
    Base.metadata,
    Column("user_id", Integer, ForeignKey(f"{USERS_TABLE_NAME}.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey(f"{NEWS_ARTICLES_TABLE_NAME}.id"), primary_key=True
    ),
)

class User(Base):
    __tablename__ = USERS_TABLE_NAME
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(MAX_USERNAME_LENGTH), unique=True, nullable=False)
    hashed_password = Column(String(MAX_PASSWORD_HASH_LENGTH), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )

class NewsArticle(Base):
    __tablename__ = NEWS_ARTICLES_TABLE_NAME
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )