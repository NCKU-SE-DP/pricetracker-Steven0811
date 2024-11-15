from sqlalchemy.orm import Session
from src.models import NewsArticle, user_news_association_table
from urllib.parse import quote
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
import json
from sqlalchemy import delete, insert, select
from src.news.constants import UDN_API_URL
from src.config import AI

class NewsService:
    def add_news_to_db(self, news_data):
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
        session = Session()
        session.add(NewsArticle(
            url=news_data["url"],
            title=news_data["title"],
            time=news_data["time"],
            content=" ".join(news_data["content"]),
            summary=news_data["summary"],
            reason=news_data["reason"],
        ))
        session.commit()
        session.close()

    def get_new_info(self, search_term, is_initial=False):
        """
        Retrieve news articles based on a search term.

        :param search_term: The term to search for in news articles.
        :param is_initial: A boolean flag indicating whether to fetch multiple pages
                        of news data.
        :return: A list of news articles matching the search term.
        """
        all_news_data = []
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

    def get_and_summarize_news(self, is_initial=False):
        """
        Retrieve and summarize news articles.

        :param is_initial: A boolean flag indicating whether to fetch multiple pages
                        of news data for the initial run.
        :return: None
        """
        news_data = self.get_new_info("價格", is_initial=is_initial)
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
            relevance = evaluate_ai.choices[AI.FIRST_CHOICE_INDEX].message.content
            if relevance == "high":
                response = requests.get(news["titleLink"])
                soup = BeautifulSoup(response.text, "html.parser")
                article_title = soup.find("h1", class_="article-content__title").text
                time = soup.find("time", class_="article-content__time").text
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
                summary_result = json.load(summarize_ai.choices[AI.FIRST_CHOICE_INDEX].message.content)
                detailed_news["summary"] = summary_result["影響"]
                detailed_news["reason"] = summary_result["原因"]
                self.add_news_to_db(detailed_news)

    def get_article_upvote_details(self, article_id, uid, news_db:Session):
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

    def news_exists(self, article_id, news_db: Session):
        return news_db.query(NewsArticle).filter_by(id=article_id).first() is not None

    def toggle_upvote(self, article_id, user_id, news_db):
        """
        Toggle the upvote status of a news article for a specific user.

        :param article_id: The ID of the news article to be upvoted or un-upvoted.
        :param user_id: The ID of the user toggling the upvote.
        :param db: The database session dependency.
        :return: A message indicating whether the article was upvoted or un-upvoted.
        """
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