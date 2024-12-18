"""
UDN News Scraper Module

This module provides the UDNCrawler class for fetching, parsing, and saving news articles from the UDN website.
The class extends the NewsCrawlerBase and includes functionalities to search for news articles based on a search term,
parse the details of individual articles, and save them to a database using SQLAlchemy ORM.

Classes:
    UDNCrawler: A class to scrape news from UDN.

Exceptions:
    DomainMismatchException: Raised when the URL domain does not match the expected domain for the crawler.

Usage Example:
    crawler = UDNCrawler(timeout=10)
    headlines = crawler.startup("technology")
    for headline in headlines:
        news = crawler.parse(headline.url)
        crawler.save(news, db_session)

UDNCrawler Methods:
    __init__(self, timeout: int = 5): Initializes the crawler with a default timeout for HTTP requests.
    startup(self, search_term: str) -> list[Headline]: Fetches news headlines for a given search term across multiple pages.
    get_headline(self, search_term: str, page: int | tuple[int, int]) -> list[Headline]: Fetches news headlines for specified pages.
    _fetch_news(self, page: int, search_term: str) -> list[Headline]: Helper method to fetch news headlines for a specific page.
    _create_search_params(self, page: int, search_term: str): Creates the parameters for the search request.
    _perform_request(self, params: dict): Performs the HTTP request to fetch news data.
    _parse_headlines(response): Parses the response to extract headlines.
    parse(self, url: str) -> News: Parses a news article from a given URL.
    _extract_news(soup, url: str) -> News: Extracts news details from the BeautifulSoup object.
    save(self, news: News, db: Session): Saves a news article to the database.
    _commit_changes(db: Session): Commits the changes to the database with error handling.
"""

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from .crawler_base import NewsCrawlerBase, Headline, News, NewsWithSummary
from fastapi import HTTPException

class UDNCrawler(NewsCrawlerBase):
    CHANNEL_ID = 2

    def __init__(self, timeout: int = 5) -> None:
        self.news_website_url = "https://udn.com/api/more"
        self.timeout = timeout

    def startup(self, search_term: str) -> list[Headline]:
        """
        Initializes the application by fetching news headlines for a given search term across multiple pages.
        This method is typically called at the beginning of the program when there is no data available,
        hence it fetches headlines from the first 10 pages.

        :param search_term: The term to search for in news headlines.
        :return: A list of Headline namedtuples containing the title and URL of news articles.
        :rtype: list[Headline]
        """
        return self.get_headline(search_term, page=(1, 10))

    def get_headline(
        self, search_term: str, page: int | tuple[int, int]
    ) -> list[Headline]:

        # Calculate the range of pages to fetch news from.
        # If 'page' is a tuple, unpack it and create a range representing those pages (inclusive).
        # If 'page' is an int, create a list containing only that single page number.
        # page_range = range(*page) if isinstance(page, tuple) else [page]
        try:
            if isinstance(page, tuple):
                start_page, end_page = page
                page_range = range(start_page, end_page + 1)
            else:
                page_range = [page]

            headlines = []
            for page_num in page_range:
                headlines.extend(self._fetch_news(page_num, search_term))

            return headlines
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail="Failed to fetch news from external source.")

    def _fetch_news(self, page: int, search_term: str) -> list[Headline]:
        params = self._create_search_params(page, search_term)
        response = self._perform_request(params=params)
        headlines = self._parse_headlines(response)
        return headlines

    def _create_search_params(self, page: int, search_term: str) -> dict:
        try:
            return {
                "page": page,
                "id": f"search:{search_term}",
                "channelId": self.CHANNEL_ID,
                "type": "searchword",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    def _perform_request(self, url: str | None = None, params: dict | None = None) -> requests.Response:
        try:
            url = url or self.news_website_url
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response
        
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail="Failed to perform request to external source.")

    @staticmethod
    def _parse_headlines(response: requests.Response) -> list[Headline]:
        try:
            data = response.json()
            headlines = []
            for news_item in data["lists"]:
                headline = Headline(
                    title=news_item["title"],
                    url=news_item["titleLink"],
                )
                headlines.append(headline)
            return headlines
        
        except ValueError as e:
            raise HTTPException(status_code=502, detail="Failed to parse news data from external source.")

    def parse(self, url: str) -> News:
        response = self._perform_request(url=url)
        soup = BeautifulSoup(response.text, "html.parser")
        news = self._extract_news(soup, url)
        return news

    @staticmethod
    def _extract_news(soup: BeautifulSoup, url: str) -> News:
        try:
            article_title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            content_section = soup.find("section", class_="article-content__editor")
            content = " ".join(
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            )

            return News(
                url=url,
                title=article_title,
                time=time,
                content=content,
            )
        except AttributeError as e:
            raise HTTPException(status_code=502, detail="Failed to extract news data from external source.")

    def save(self, news: NewsWithSummary, db: Session):
        db.add(news)
        self._commit_changes(db)

    @staticmethod
    def _commit_changes(db: Session):
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to commit changes to the database.")
