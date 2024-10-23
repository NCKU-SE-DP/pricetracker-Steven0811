import json
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
import itertools
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, sessionmaker
from typing import List, Optional
import requests
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
import os
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from pydantic import BaseModel, Field, AnyHttpUrl
from sqlalchemy import (Column, ForeignKey, Integer, String, Table, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

USERS_TABLE_NAME = "users"
USER_NEWS_UPVOTES_TABLE_NAME = "user_news_upvotes"
NEWS_ARTICLES_TABLE_NAME = "news_articles"
user_news_association_table = Table(
    USER_NEWS_UPVOTES_TABLE_NAME,
    Base.metadata,
    Column("user_id", Integer, ForeignKey(f"{USERS_TABLE_NAME}.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey(f"{NEWS_ARTICLES_TABLE_NAME}.id"), primary_key=True
    ),
)

# from pydantic import BaseModel
MAX_USERNAME_LENGTH= 50
MAX_PASSWORD_LENGTH = 200
NEWS_ARTICLE_MODEL_NAME = "NewsArticle"
UPVOTED_BY_USERS_RELATIONSHIP = "upvoted_by_users"


class User(Base):
    __tablename__ = USERS_TABLE_NAME
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(MAX_USERNAME_LENGTH), unique=True, nullable=False)
    hashed_password = Column(String(MAX_PASSWORD_LENGTH), nullable=False)
    upvoted_news = relationship(
        NEWS_ARTICLE_MODEL_NAME,
        secondary=user_news_association_table,
        back_populates=UPVOTED_BY_USERS_RELATIONSHIP,
    )

USER_MODEL_NAME = "User"
UPVOTED_NEWS_RELATIONSHIP = "upvoted_news"
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
        USER_MODEL_NAME, secondary=user_news_association_table, back_populates=UPVOTED_BY_USERS_RELATIONSHIP
    )

DATABASE_URL = "sqlite:///news_database.db"
engine = create_engine(DATABASE_URL, echo=True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

sentry_sdk.init(
    dsn="https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
background_scheduler = BackgroundScheduler()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

ALLOW_ORIGIN = "http://localhost:8080"
app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=[ALLOW_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from openai import OpenAI


# def generate_summary(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content

#
# def extract_search_keywords(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content


from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session


def add_news_to_db(news_data):
    """
    add new to db
    :param news_data: news info
    :return:
    """
    session = Session()
    session.add(NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),  # 將內容list轉換為字串
        summary=news_data["summary"],
        reason=news_data["reason"],
    ))
    session.commit()
    session.close()

UDN_API_URL = "https://udn.com/api/more"
def get_new_info(search_term, is_initial=False):
    """
    get new

    :param search_term:
    :param is_initial:
    :return:
    """
    all_news_data = []
    # iterate pages to get more news data, not actually get all news data
    if is_initial:
        news_lists_by_page = []
        START_PAGE = 1
        END_PAGE = 9
        for page in range(START_PAGE, END_PAGE+1):
            page_params = {
                "page": page,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get(UDN_API_URL, params=page_params)
            news_lists_by_page.append(response.json()["lists"])

        for news_list in news_lists_by_page:
            all_news_data.append(news_list)
    else:
        initial_page_params = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get(UDN_API_URL, params=initial_page_params)

        all_news_data = response.json()["lists"]
    return all_news_data

def get_and_summarize_news(is_initial=False):
    """
    get new info

    :param is_initial:
    :return:
    """
    news_data = get_new_info("價格", is_initial=is_initial)
    for news in news_data:
        news_title = news["title"]
        evaluation_request_payload = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": f"{news_title}"},
        ]
        evaluate_ai = OpenAI(api_key="xxx").chat.completions.create(
            model = "gpt-3.5-turbo",
            messages = evaluation_request_payload,
        )
        FIRST_CHOICE_INDEX = 0
        relevance = evaluate_ai.choices[FIRST_CHOICE_INDEX].message.content
        if relevance == "high":
            response = requests.get(news["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            # 標題
            article_title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            # 定位到包含文章内容的 <section>
            content_section = soup.find("section", class_="article-content__editor")

            article_aragraphs = [
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            detailed_news =  {
                "url": news["titleLink"],
                "title": article_title,
                "time": time,
                "content": article_aragraphs,
            }
            summary_request_payload = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "user", "content": " ".join(detailed_news["content"])},
            ]

            summarize_ai = OpenAI(api_key="xxx").chat.completions.create(
                model="gpt-3.5-turbo",
                messages=summary_request_payload,
            )
            summary_result = json.load(summarize_ai.choices[FIRST_CHOICE_INDEX].message.content)
            # result = json.loads(result)
            detailed_news["summary"] = summary_result["影響"]
            detailed_news["reason"] = summary_result["原因"]
            add_news_to_db(detailed_news)


@app.on_event("startup")
def start_scheduler():
    news_db = SessionLocal()
    if news_db.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        get_and_summarize_news()
    news_db.close()
    SCHEDULER_INTERVAL_MINUTES = 100
    background_scheduler.add_job(get_and_summarize_news, "interval", minutes=SCHEDULER_INTERVAL_MINUTES)
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TOKER_URL = "/api/v1/users/login"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKER_URL)


def session_opener():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()



def verify(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


def check_user_password_is_correct(user_db, username, password):
    user = user_db.query(User).filter(User.username == username).first()
    if not verify(password, user.hashed_password):
        return False
    return user

JWT_SECRET_KEY = '1892dhianiandowqd0n'
def authenticate_user_token(
    token = Depends(oauth2_scheme),
    user_db = Depends(session_opener)
):
    key = '1892dhianiandowqd0n'
    payload = jwt.decode(token, key, algorithms=["HS256"])
    return user_db.query(User).filter(User.username == payload.get("sub")).first()


def create_access_token(user_data, expires_delta=None):
    """create access token"""
    to_encode = user_data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
        expire = datetime.utcnow() + timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


@app.post("/api/v1/users/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), user_db: Session = Depends(session_opener)
):
    """login"""
    user = check_user_password_is_correct(user_db, form_data.username, form_data.password)
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

class UserAuthSchema(BaseModel):
    username: str
    password: str
@app.post("/api/v1/users/register")
def create_user(user: UserAuthSchema, user_db: Session = Depends(session_opener)):
    """create user"""
    hashed_password = password_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    user_db.add(new_user)
    user_db.commit()
    user_db.refresh(new_user)
    return new_user


@app.get("/api/v1/users/me")
def read_users_me(user=Depends(authenticate_user_token)):
    return {"username": user.username}

ID_COUNTER_START = 1000000
_id_counter = itertools.count(start=ID_COUNTER_START)


def get_article_upvote_details(article_id, uid, news_db):
    upvote_count = (
        news_db.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    voted = False
    if uid:
        voted = (
                news_db.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=uid)
                .first()
                is not None
        )
    return upvote_count, voted


@app.get("/api/v1/news/news")
def read_news(news_db=Depends(session_opener)):
    """
    read new

    :param db:
    :return:
    """
    news = news_db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    formatted_news = []
    for article in news:
        upvote_count, is_upvoted = get_article_upvote_details(article.id, None, news_db)
        formatted_news.append(
            {**article.__dict__, "upvotes": upvote_count, "is_upvoted": is_upvoted}
        )
    return formatted_news


@app.get(
    "/api/v1/news/user_news"
)
def read_user_news(
        news_db=Depends(session_opener),
        user=Depends(authenticate_user_token)
):
    """
    read user new

    :param db:
    :param u:
    :return:
    """
    news = news_db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    user_news_data = []
    for article in news:
        upvotes, upvoted = get_article_upvote_details(article.id, user.id, news_db)
        user_news_data.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": upvoted,
            }
        )
    return user_news_data

class PromptRequest(BaseModel):
    prompt: str

@app.post("/api/v1/news/search_news")
async def search_news(request: PromptRequest):
    user_prompt = request.prompt
    news_list = []
    search_request_payload = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{user_prompt}"},
    ]

    search_ai = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=search_request_payload,
    )
    FIRST_CHOICE_INDEX = 0
    keywords = search_ai.choices[FIRST_CHOICE_INDEX].message.content
    # should change into simple factory pattern
    news_items = get_new_info(keywords, is_initial=False)
    for news in news_items:
        try:
            response = requests.get(news["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            # 標題
            article_title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            # 定位到包含文章内容的 <section>
            content_section = soup.find("section", class_="article-content__editor")

            article_paragraphs = [
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            detailed_news = {
                "url": news["titleLink"],
                "title": article_title,
                "time": time,
                "content": article_paragraphs,
            }
            detailed_news["content"] = " ".join(detailed_news["content"])
            detailed_news["id"] = next(_id_counter)
            news_list.append(detailed_news)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

class NewsSumaryRequestSchema(BaseModel):
    content: str

@app.post("/api/v1/news/news_summary")
async def news_summary(
        payload: NewsSumaryRequestSchema, user=Depends(authenticate_user_token)
):
    response = {}
    summary_request_payload = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    summarize_ai = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=summary_request_payload,
    )
    FIRST_CHOICE_INDEX = 0
    summary_result = summarize_ai.choices[FIRST_CHOICE_INDEX].message.content
    if summary_result:
        summary_result = json.loads(summary_result)
        response["summary"] = summary_result["影響"]
        response["reason"] = summary_result["原因"]
    return response

@app.post("/api/v1/news/{id}/upvote")
def upvote_article(
        article_id,
        news_db=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    message = toggle_upvote(article_id, user.id, news_db)
    return {"message": message}

def toggle_upvote(article_id, user_id, news_db):
    existing_upvote = news_db.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == article_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        delete_statement = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == article_id,
            user_news_association_table.c.user_id == user_id,
        )
        news_db.execute(delete_statement)
        news_db.commit()
        return "Upvote removed"
    else:
        insert_statement = insert(user_news_association_table).values(
            news_articles_id=article_id, user_id=user_id
        )
        news_db.execute(insert_statement)
        news_db.commit()
        return "Article upvoted"


def news_exists(article_id, news_db: Session):
    return news_db.query(NewsArticle).filter_by(id=article_id).first() is not None


@app.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
        category_name=Query(None), commodity_name=Query(None)
):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category_name, "Name": commodity_name},
    ).json()
