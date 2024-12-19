from sqlalchemy.orm import Session
from src.models import NewsArticle, user_news_association_table
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException
from src.crawler.udn_crawler import UDNCrawler
from src.crawler.crawler_base import NewsWithSummary
from src.llm_client.llm_client import OpenAIClient
from src.llm_client.config import OpenAIConfig
from src.error_handler.logger import Logger
import requests

udn_crawler = UDNCrawler()
openai_client = OpenAIClient(OpenAIConfig.api_key)

def add_news_to_db(news_data):
    """
    Add a news article to the database.

    :param news_data: A dictionary containing the news article data. Expected keys are:
                      - url: The URL of the news article.
                      - title: The title of the news article.
                      - time: The publication time of the news article.
                      - content: The content of the news article.
                      - summary: The summary of the news article.
                      - reason: The reason or context of the news article.
    :param session: The database session dependency, injected by FastAPI.
    :return: None
    """
    udn_crawler.save(news_data)

def get_new_info(search_term, is_initial=False):
    """
    Retrieve news articles based on a search term.

    :param search_term: The term to search for in news articles.
    :param is_initial: A boolean flag indicating whether to fetch multiple pages
                       of news data.
    :return: A list of news articles matching the search term.
    """
    start_page = 1
    end_page = 9 if is_initial else 1
    return udn_crawler.get_headline(search_term, page=(start_page, end_page))

def get_and_summarize_news(is_initial=False):
    """
    Retrieve and summarize news articles.

    :param is_initial: A boolean flag indicating whether to fetch multiple pages
                       of news data for the initial run.
    :return: None
    """
    logger = Logger(__name__, "get_and_summarize_news").get_logger()
    logger.info("Fetching news data...")
    news_data = get_new_info("價格", is_initial=is_initial)
    for news in news_data:
        news_title = news["title"]
        relevance = openai_client.evaluate_relevance(news_title)
        if relevance == "high":
            detailed_news = udn_crawler.validate_and_parse(news["titleLink"])
            
            summary_result = openai_client.generate_summary(detailed_news["content"])

            summarized_news = NewsWithSummary(**detailed_news)
            summarized_news["summary"] = summary_result["影響"]
            summarized_news["reason"] = summary_result["原因"]
            add_news_to_db(summarized_news)

def get_article_upvote_details(article_id, uid, news_db):
    """
    Retrieve the upvote details for a specific news article.

    :param article_id: The ID of the news article.
    :param user_id: The ID of the user (optional). If provided, the function
                    will check if this user has upvoted the article.
    :param db: The database session dependency.
    :return: A tuple containing the number of upvotes and a boolean indicating
             whether the user has upvoted the article.
    """
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

def news_exists(article_id, news_db: Session):
    try:
        return news_db.query(NewsArticle).filter_by(id=article_id).first() is not None
    except SQLAlchemyError as db_err:
        raise HTTPException(status_code=500, detail="Failed to check article existence.")

def toggle_upvote(article_id, user_id, news_db):
    """
    Toggle the upvote status of a news article for a specific user.

    :param article_id: The ID of the news article to be upvoted or un-upvoted.
    :param user_id: The ID of the user toggling the upvote.
    :param db: The database session dependency.
    :return: A message indicating whether the article was upvoted or un-upvoted.
    """
    logger = Logger(__name__, "toggle_upvote").get_logger()
    try:
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
            logger.info("Upvote removed.")
            return "Upvote removed"
        else:
            insert_statement = insert(user_news_association_table).values(
                news_articles_id=article_id, user_id=user_id
            )
            news_db.execute(insert_statement)
            news_db.commit()
            logger.info("Article upvoted.")
            return "Article upvoted"
    except IntegrityError as ie:
        raise HTTPException(status_code=400, detail="Invalid data for upvote operation.")
    except SQLAlchemyError as db_err:
        raise HTTPException(status_code=500, detail="Failed to toggle upvote.")