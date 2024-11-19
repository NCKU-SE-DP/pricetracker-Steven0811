from fastapi import APIRouter, Depends
from src.models import NewsArticle
from src.database import session_opener
from src.news.schemas import NewsSumaryRequestSchema, PromptRequest
from src.auth.dependencies import AuthDependency
from src.news.service import NewsService
import requests
from bs4 import BeautifulSoup
import json
from src.news.utils import NewsUtils
from src.config import AI

class NewsRouter(NewsService, AuthDependency, NewsUtils):
    def __init__(self):
        super().__init__()
        
        self.news_router = APIRouter(
            prefix="/news",
            tags=["news"],
            responses={404: {"description": "Not found"}},
        )

        @self.news_router.get("/news")
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
                upvote_count, is_upvoted = self.get_article_upvote_details(article.id, None, news_db)
                formatted_news.append(
                    {**article.__dict__, "upvotes": upvote_count, "is_upvoted": is_upvoted}
                )
            return formatted_news


        @self.news_router.get("/user_news")
        def read_user_news(
                news_db=Depends(session_opener),
                user=Depends(self.authenticate_user_token)
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
                upvotes, upvoted = self.get_article_upvote_details(article.id, user.id, news_db)
                user_news_data.append(
                    {
                        **article.__dict__,
                        "upvotes": upvotes,
                        "is_upvoted": upvoted,
                    }
                )
            return user_news_data

        @self.news_router.post("/search_news")
        async def search_news(request: PromptRequest):
            """
            Search for news articles based on user input and extract relevant keywords.

            :param request: The request body containing the user prompt.
            :return: A list of news articles matching the extracted keywords.
            """
            user_prompt = request.prompt
            news_list = []
            search_request_payload = [
                {
                    "role": "system",
                    "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
                },
                {"role": "user", "content": f"{user_prompt}"},
            ]

            search_ai = self.generate_ai(search_request_payload)
            keywords = search_ai.choices[AI.FIRST_CHOICE_INDEX].message.content
            news_items = self.get_new_info(keywords, is_initial=False)
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
                    detailed_news["id"] = next(self._id_counter)
                    news_list.append(detailed_news)
                except Exception as e:
                    print(e)
            return sorted(news_list, key=lambda x: x["time"], reverse=True)

        @self.news_router.post("/news_summary")
        async def news_summary(
                payload: NewsSumaryRequestSchema, user=Depends(self.authenticate_user_token)
        ):
            """
            Generate a summary of the news article content provided by the user.

            :param payload: The request body containing the content of the news article.
            :param user: The authenticated user dependency, injected by FastAPI.
            :return: A dictionary containing the summary and the main reasons mentioned
                    in the article.
            """
            response = {}
            summary_request_payload = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "user", "content": f"{payload.content}"},
            ]

            summarize_ai = self.generate_ai(summary_request_payload)
            summary_result = summarize_ai.choices[AI.FIRST_CHOICE_INDEX].message.content
            if summary_result:
                summary_result = json.loads(summary_result)
                response["summary"] = summary_result["影響"]
                response["reason"] = summary_result["原因"]
            return response

        @self.news_router.post("/{id}/upvote")
        def upvote_article(
                id,
                news_db=Depends(session_opener),
                user=Depends(self.authenticate_user_token),
        ):
            """
            Toggle the upvote status of a news article for the authenticated user.

            :param article_id: The ID of the news article to be upvoted or un-upvoted.
            :param news_db: The database session dependency, injected by FastAPI.
            :param user: The authenticated user dependency, injected by FastAPI.
            :return: A dictionary containing a message indicating the result of the
                    upvote action.
            """
            message = self.toggle_upvote(id, user.id, news_db)
            return {"message": message}