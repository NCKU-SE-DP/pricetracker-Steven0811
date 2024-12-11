from fastapi import APIRouter, Depends, HTTPException, status
from src.models import NewsArticle
from src.database import session_opener
from src.news.schemas import NewsSumaryRequestSchema, PromptRequest, NewsSumaryCustomModelSchema
from src.auth.dependencies import authenticate_user_token
from src.news.service import get_article_upvote_details, toggle_upvote, get_new_info
import json
import requests
from bs4 import BeautifulSoup
from src.news.utils import _id_counter
from src.llm_client.llm_client import OpenAIClient, AnthropicAIClient
from src.crawler.udn_crawler import UDNCrawler
from src.llm_client.config import OpenAIConfig, AnthropicConfig

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
    news = news_db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
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
        try:
            response = requests.get(news["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            article_title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
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
p
@router.post("/news_summary")
async def news_summary(
        payload: NewsSumaryRequestSchema, user=Depends(authenticate_user_token)
):
    """
    Generate a summary of the news article content provided by the user.

    :param payload: The request body containing the content of the news article.
    :param user: The authenticated user dependency, injected by FastAPI.
    :return: A dictionary containing the summary and the main reasons mentioned
             in the article.
    """
    response = {}
    summary_result = openai_client.generate_summary(payload.content)
    if summary_result:
        summary_result = json.loads(summary_result)
        response["summary"] = summary_result["影響"]
        response["reason"] = summary_result["原因"]
    return response

@router.post("/news_summary_custom_model")
async def news_summary_custom_model(
        payload: NewsSumaryCustomModelSchema, user=Depends(authenticate_user_token)
):
    if payload.ai_model == OpenAIConfig.model:
        client = OpenAIClient(OpenAIConfig.api_key)
    elif payload.ai_model == AnthropicConfig.model:
        client = AnthropicAIClient(AnthropicConfig.api_key)
    else:
        raise ValueError("Invalid model specified.")
    
    try:
        response = {}
        summary_result = client.generate_summary(payload.content)
        if summary_result:
            summary_result = json.loads(summary_result)
            response["summary"] = summary_result["影響"]
            response["reason"] = summary_result["原因"]
        return response
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error decoding JSON response.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

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