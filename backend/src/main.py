import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from src.database import SessionLocal
from src.models import  NewsArticle
from src.config import Sentry, Basic
from src.users.router import UsersRouter
from src.news.router import NewsRouter
from src.prices.router import PricesRouter
from src.news.service import NewsService


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

news_service = NewsService()
@app.on_event("startup")
def start_scheduler():
    news_db = SessionLocal()
    if news_db.query(NewsArticle).count() == 0:
        news_service.get_and_summarize_news()
    news_db.close()
    background_scheduler.add_job(news_service.get_and_summarize_news, "interval", minutes=Basic.SCHEDULER_INTERVAL_MINUTES)
    background_scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()

class Router(NewsRouter, UsersRouter, PricesRouter, Basic):
    def __init__(self):
        NewsRouter.__init__(self)
        UsersRouter.__init__(self)
        PricesRouter.__init__(self)
        Basic.__init__(self)

app.include_router(Router().users_router, prefix=Router().API_PREFIX)
app.include_router(Router().news_router, prefix=Router().API_PREFIX)
app.include_router(Router().prices_router, prefix=Router().API_PREFIX)