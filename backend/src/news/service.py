from sqlalchemy.orm import Session
from src.models import NewsArticle, user_news_association_table
from urllib.parse import quote
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
import json
from sqlalchemy import delete, insert, select
from src.news.constants import UDN_API_URL

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

def news_exists(article_id, news_db: Session):
    return news_db.query(NewsArticle).filter_by(id=article_id).first() is not None

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