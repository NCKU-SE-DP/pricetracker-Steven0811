import abc

from .exceptions import DomainMismatchException

from pydantic import BaseModel, Field
from openai import OpenAI

from src.config import AI


class MessagePassingInterfaceExample(BaseModel):
    key: str = Field(
        default=...,
        example="example",
        description="description"
    )
    

class LLMClientBase(metaclass=abc.ABCMeta):
    _api_key : str
    
    @abc.abstractmethod
    def evaluate_relevance(self, keywords: str) -> str:
        """
        Evaluate the relevance of a given news title or content with respect to a specific topic.

        This method takes an input payload in the form of a string, representing the news title 
        or content. It evaluates whether the input is relevant to a predefined topic, such as 
        "changes in the prices of daily necessities." The relevance is classified into one of 
        three categories: 'high', 'medium', or 'low'.

        :param evaluation_payload: The news title or content to evaluate.

        :return: The relevance of the input payload to the predefined topic.
        """
        return NotImplemented
    
    @abc.abstractmethod
    def generate_summary(self, news_content: str) -> str:
        """
        Generate a summary of a given news article content.

        This method takes an input payload in the form of a string, representing the content
        of a news article. It generates a summary of the main impact and key reasons mentioned
        in the article. The summary is returned as a string in JSON format.

        :param news_content: The content of the news article.

        :return: A JSON-formatted string containing the summary of the news article.
        """
        return NotImplemented
    
    @staticmethod
    @abc.abstractmethod
    def extract_search_keywords(text: str) -> str:
        """
        Extract search keywords from a given text.

        This method takes an input payload in the form of a string, representing a piece of text
        that describes the desired news content. It extracts the most important keywords from the
        input text to facilitate search queries. The extracted keywords are returned as a string
        separated by spaces.

        :param text: The input text containing the desired news content.

        :return: A string containing the extracted search keywords.
        """
        return NotImplemented
    
    @staticmethod
    def _generate_text(message: list[dict[str, str]]) -> str:
        """
        Generate text based on the given message.

        This method takes a list of dictionaries, where each dictionary contains the role and content
        of a message. It generates a text response based on the given messages.

        :param message: A list of dictionaries containing the role and content of messages.

        :return: A string representing the generated text response.
        """

        ai = OpenAI(api_key="xxx").chat.completions.create(
            model = AI.AI_MODEL,
            messages = message,
        )

        return ai.choices[AI.FIRST_CHOICE_INDEX].message.content