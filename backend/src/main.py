import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from src.database import SessionLocal
from src.models import  NewsArticle
from src.config import Sentry, Basic
from src.users.router import router as users_router
from src.news.router import router as news_router
from src.prices.router import router as prices_router
from src.news.service import get_and_summarize_news

sentry_sdk.init(
    dsn = Sentry.DSN,
    traces_sample_rate = Sentry.TRACE_SAMPLE_RATE,
    profiles_sample_rate = Sentry.PROFILES_SAMPLE_RATE,
)

app = FastAPI()
background_scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[Basic.ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def start_scheduler():
    news_db = SessionLocal()
    if news_db.query(NewsArticle).count() == 0:
        get_and_summarize_news()
    news_db.close()
    background_scheduler.add_job(get_and_summarize_news, "interval", minutes=Basic.SCHEDULER_INTERVAL_MINUTES)
    background_scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()

app.include_router(users_router, prefix=Basic.API_PREFIX)
app.include_router(news_router, prefix=Basic.API_PREFIX)
app.include_router(prices_router, prefix=Basic.API_PREFIX)