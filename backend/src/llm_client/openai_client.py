from openai import OpenAI
from src.llm_client.base import LLMClientBase, MessagePassingInterface
from src.llm_client.config import AI, Prompt

class OpenAIClient(LLMClientBase):
    def __init__(self, _api_key: str):
        super().__init__()
        self._api_key = _api_key

    def _generate_ai(self, message: MessagePassingInterface) -> OpenAI:
        ai = OpenAI(api_key=self._api_key).chat.completions.create(
            model = AI.AI_MODEL,
            messages = message,
        )
        return ai

    def extract_search_keywords(self, text: str) -> str:
        message = MessagePassingInterface(
            system_content=Prompt.keyword_prompt,
            user_content=text
        )
        extract_ai = self._generate_ai(message.to_dict)
        return self._generate_text(extract_ai)

    def evaluate_relevance(self, title: str) -> str:
        message = MessagePassingInterface(
            system_content=Prompt.relevance_prompt,
            user_content=title
        )
        evaluate_ai = self._generate_ai(message.to_dict)
        
        return self._generate_text(evaluate_ai)

    def generate_summary(self, content: str) -> str:
        message = MessagePassingInterface(
            system_content=Prompt.summary_prompt,
            user_content=content
        )
        summarize_ai = self._generate_ai(message.to_dict)
        
        return self._generate_text(summarize_ai)