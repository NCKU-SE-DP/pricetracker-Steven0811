import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
import json
from jose import jwt
from src.main import app
from src.database import Base
from src.models import User, NewsArticle
from src.database import session_opener
from src.news.schemas import NewsSumaryRequestSchema, NewsSumaryCustomModelSchema
from src.auth.service import pwd_context
from unittest.mock import Mock


SECRET_KEY = "1892dhianiandowqd0n"
ALGORITHM = "HS256"
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_session_opener():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[session_opener] = override_session_opener
client = TestClient(app)

@pytest.fixture(scope="module")
def clear_users():
    with next(override_session_opener()) as db:
        db.query(User).delete()
        db.commit()

@pytest.fixture(scope="module")
def test_user(clear_users):
    hashed_password = pwd_context.hash("testpassword")

    with next(override_session_opener()) as db:
        user = User(username="testuser", hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


@pytest.fixture(scope="module")
def test_token(test_user):
    access_token = jwt.encode({"sub": test_user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return access_token


@pytest.fixture(scope="module")
def test_articles():
    with next(override_session_opener()) as db:
        article_1 = NewsArticle(
            url="https://example.com/test-news-1",
            title="Test News 1",
            content="This is test content 1",
            time="2024-01-01",
            summary="Test summary 1",
            reason="Test reason 1"
        )
        article_2 = NewsArticle(
            url="https://example.com/test-news-2",
            title="Test News 2",
            content="This is test content 2",
            time="2024-01-02",
            summary="Test summary 2",
            reason="Test reason 2"
        )
        db.add_all([article_1, article_2])
        db.commit()
        db.refresh(article_1)
        db.refresh(article_2)

        return [article_1, article_2]


@pytest.fixture(scope="module")
def test_user_and_articles(test_user, test_articles):
    return test_user, test_articles


def test_read_news(test_articles):
    response = client.get("/api/v1/news/news")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2
    assert json_response[0]["title"] == "Test News 2"
    assert json_response[1]["title"] == "Test News 1"


def test_read_user_news(test_user, test_token, test_articles):
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.get("/api/v1/news/user_news", headers=headers)
    print(test_token)
    print(response.json())
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2
    assert json_response[0]["title"] == "Test News 2"
    assert json_response[0]["is_upvoted"] is False
    assert json_response[1]["title"] == "Test News 1"
    assert json_response[1]["is_upvoted"] is False

def mock_openai(mocker, return_content):
    mock_generate = mocker.patch('src.llm_client.llm_client.OpenAIClient._generate_text')
    
    mock_generate.return_value = return_content

def mock_anthropic(mocker, return_content):
    mock_generate = mocker.patch('src.llm_client.llm_client.AnthropicAIClient._generate_text')
    
    mock_generate.return_value = return_content

def test_search_news(mocker):
    mock_openai(mocker, "keywords")

    mock_get_new_info = mocker.patch("src.news.router.get_new_info", return_value=[
        {"titleLink": "http://example.com/news1"}
    ])

    mock_get = mocker.patch("src.news.service.requests.get", return_value=mocker.Mock(
        text="""
        <html>
        <h1 class="article-content__title">Test Title</h1>
        <time class="article-content__time">2024-09-10</time>
        <section class="article-content__editor">
            <p>This is a test paragraph.</p>
        </section>
        </html>
        """
    ))

    request_body = {"prompt": "Test search prompt"}

    response = client.post("/api/v1/news/search_news", json=request_body)

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Title"
    assert data[0]["time"] == "2024-09-10"
    assert data[0]["content"] == "This is a test paragraph."

def test_news_summary_custom_model(mocker, test_token):
    headers = {"Authorization": f"Bearer {test_token}"}

    openai_response = json.dumps({"影響": "test impact(OpenAI)", "原因": "test reason(OpenAI)"})
    mock_openai(mocker, openai_response)

    request_body = NewsSumaryCustomModelSchema(content="Test news content", ai_model="openai:gpt-3.5-turbo")
    response = client.post("/api/v1/news/news_summary_custom_model", json=request_body.dict(), headers=headers)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["summary"] == "test impact(OpenAI)"
    assert json_response["reason"] == "test reason(OpenAI)"

    anthropic_response = json.dumps({"影響": "test impact(Anthropic)", "原因": "test reason(Anthropic)"})
    mock_anthropic(mocker, anthropic_response)

    request_body = NewsSumaryCustomModelSchema(content="Test news content", ai_model="anthropic:claude-3-5-sonnet-20240620")
    response = client.post("/api/v1/news/news_summary_custom_model", json=request_body.dict(), headers=headers)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["summary"] == "test impact(Anthropic)"
    assert json_response["reason"] == "test reason(Anthropic)"

def test_upvote_article(test_user_and_articles, test_token):
    user, articles = test_user_and_articles
    headers = {"Authorization": f"Bearer {test_token}"}

    response = client.post(f"/api/v1/news/{articles[0].id}/upvote", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Article upvoted"


def test_downvote_article(test_user_and_articles, test_token):
    user, articles = test_user_and_articles
    headers = {"Authorization": f"Bearer {test_token}"}

    response = client.post(f"/api/v1/news/{articles[0].id}/upvote", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Upvote removed"
