import abc
import aisuite as ai
from src.llm_client.config import Prompt

class ChatCompletionProvider:
    def __init__(self, system_content: str, user_content: str):
        self.messages = [
            {"role": "system", "content": f"{system_content}"},
            {"role": "user", "content": f"{user_content}"},
        ]
        self.temperature = 0.75

    def chat_completion_create(self, model: str, client: ai.Client) -> None:
        response = client.chat.completions.create(
            messages = self.messages, 
            model = model,
            temperature = self.temperature
        )
        return response.choices[0].message.content
    
    
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
    
    @abc.abstractmethod
    def extract_search_keywords(self, text: str) -> str:
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


class LLMClientTemplate(LLMClientBase):
    def __init__(self, _api_key: str, chat_provider_cls = ChatCompletionProvider):
        self.client = None
        self.model = None
        self._api_key = _api_key
        self.chat_provider_cls = chat_provider_cls
        self._initialize_client()

    @abc.abstractmethod
    def _initialize_client(self):
        """
        Initialize the AI client.

        This method should be implemented by subclasses to initialize the specific AI client.
        """
        return NotImplemented
    
    def _generate_text(self,system_content: str, user_content: str) -> None:
        try:
            chat_provider = self.chat_provider_cls(
                system_content=system_content,
                user_content=user_content
            )
            return chat_provider.chat_completion_create(self.model, self.client)
        
        except Exception as error:
            raise ValueError(f"[LLMClientTemplate] Chat provider creation failed: {error}")
        
    def evaluate_relevance(self, title: str) -> str:
        return self._generate_text(Prompt.relevance_prompt, title)
    
    def generate_summary(self, content: str) -> str:
        return self._generate_text(Prompt.summary_prompt, content)
    
    def extract_search_keywords(self, text: str) -> str:
        return self._generate_text(Prompt.keyword_prompt, text)