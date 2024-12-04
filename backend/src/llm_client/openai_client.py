from openai import OpenAI
from src.llm_client.base import LLMClientBase
from src.llm_client.config import AI, Prompt

class OpenAIClient(LLMClientBase):
    def __init__(self, _api_key: str):
        super().__init__()
        self._api_key = _api_key

    def _generate_ai(self, message: list[dict[str, str]]) -> OpenAI:
        ai = OpenAI(api_key=self._api_key).chat.completions.create(
            model = AI.AI_MODEL,
            messages = message,
        )
        return ai

    def extract_search_keywords(self, text: str) -> str:
        extract_ai = self._generate_ai([
                {
                    "role": "system",
                    "content": Prompt.keyword_prompt,
                },
                {"role": "user", "content": text},
            ])
        return self._generate_text(extract_ai)

    def evaluate_relevance(self, title: str) -> str:
        evaluate_ai = self._generate_ai([
                {
                    "role": "system",
                    "content": Prompt.relevance_prompt,
                },
                {"role": "user", "content": title},
            ])
        
        return self._generate_text(evaluate_ai)

    def generate_summary(self, content: str) -> str:
        summarize_ai = self._generate_ai([
                {
                    "role": "system",
                    "content": Prompt.summary_prompt,
                },
                {"role": "user", "content": content},
            ])
        
        return self._generate_text(summarize_ai)