from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from src.models import NewsArticle
from src.database import session_opener
from src.news.schemas import PromptRequest, NewsSumaryCustomModelSchema
from src.auth.dependencies import authenticate_user_token
from src.news.service import get_article_upvote_details, toggle_upvote, get_new_info
import json
import requests
from src.news.utils import _id_counter
from src.llm_client.llm_client import OpenAIClient, AnthropicAIClient
from src.crawler.udn_crawler import UDNCrawler
from src.llm_client.config import OpenAIConfig, AnthropicConfig
from src.error_handler.logger import Logger

openai_client = OpenAIClient(OpenAIConfig.api_key)
udn_crawler = UDNCrawler()

router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)

@router.get("/news")
def read_news(news_db=Depends(session_opener)):
    """
    Retrieve all news articles, ordered by time in descending order.

    :param news_db: The database session dependency, injected by FastAPI.
    :return: A list of formatted news articles, each including the number of
             upvotes and whether the current user has upvoted the article.
    """
    try:
        news = news_db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database query failed.")
    formatted_news = []
    for article in news:
        upvote_count, is_upvoted = get_article_upvote_details(article.id, None, news_db)
        formatted_news.append(
            {**article.__dict__, "upvotes": upvote_count, "is_upvoted": is_upvoted}
        )
    return formatted_news

@router.get("/user_news")
def read_user_news(
        news_db=Depends(session_opener),
        user=Depends(authenticate_user_token)
):
    """
    Retrieve news articles related to the authenticated user, ordered by time in descending order.

    :param news_db: The database session dependency, injected by FastAPI.
    :param user: The authenticated user dependency, injected by FastAPI.
    :return: A list of formatted news articles, each including the number of
             upvotes and whether the authenticated user has upvoted the article.
    """
    logger = Logger(__name__, "read_user_news").get_logger()
    try:
        news = news_db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database query failed.")

    try:
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
    except AttributeError:
        logger.warning("User not found in request.")
        raise HTTPException(status_code=401, detail="Authentication failed. Invalid user.")
    
    logger.info("User news data retrieved successfully.")
    return user_news_data

@router.post("/search_news")
async def search_news(request: PromptRequest):
    """
    Search for news articles based on user input and extract relevant keywords.

    :param request: The request body containing the user prompt.
    :return: A list of news articles matching the extracted keywords.
    """
    user_prompt = request.prompt
    news_list = []
    keywords = openai_client.extract_search_keywords(user_prompt)
    news_items = get_new_info(keywords, is_initial=False)

    for news in news_items:
        detailed_news = udn_crawler.parse(news["titleLink"])
        detailed_news_dict = {
            "id": next(_id_counter),
            "url": detailed_news.url,
            "title": detailed_news.title,
            "time": detailed_news.time,
            "content": detailed_news.content,
        }
        news_list.append(detailed_news_dict)

    return sorted(news_list, key=lambda x: x["time"], reverse=True)

@router.post("/news_summary_custom_model")
async def news_summary_custom_model(
        payload: NewsSumaryCustomModelSchema, user=Depends(authenticate_user_token)
):
    """
    Generate a summary of the news article content using a selected AI model.

    :param payload: Request body containing the content and AI model selection.
    :param user: The authenticated user.
    :return: Summary and reasons extracted from the article content.
    """
    logger = Logger(__name__, "news_summary_custom_model").get_logger()
    if payload.ai_model == OpenAIConfig.model:
        logger.info("OpenAI model selected")
        client = OpenAIClient(OpenAIConfig.api_key)
    elif payload.ai_model == AnthropicConfig.model:
        logger.info("Anthropic model selected")
        client = AnthropicAIClient(AnthropicConfig.api_key)
    else:
        raise HTTPException(status_code=400, detail="Invalid model specified.")

    try:
        summary_result = client.generate_summary(payload.content)
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Failed to connect to the AI model API.")
    if not summary_result:
        raise HTTPException(status_code=502, detail="Failed to generate summary from AI model.")
    
    try:
        summary_result = json.loads(summary_result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Invalid response format from AI model.")
    
    response = {
        "summary": summary_result.get("影響", "No summary available"),
        "reason": summary_result.get("原因", "No reasons available")
    }
    return response
 
@router.post("/{id}/upvote")
def upvote_article(
        id,
        news_db=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    """
    Toggle the upvote status of a news article for the authenticated user.

    :param article_id: The ID of the news article to be upvoted or un-upvoted.
    :param news_db: The database session dependency, injected by FastAPI.
    :param user: The authenticated user dependency, injected by FastAPI.
    :return: A dictionary containing a message indicating the result of the
             upvote action.
    """
    message = toggle_upvote(id, user.id, news_db)
    return {"message": message}