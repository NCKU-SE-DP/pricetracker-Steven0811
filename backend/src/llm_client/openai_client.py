from openai import OpenAI
from src.llm_client.base import LLMClientBase
from src.config import AI

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
                    "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
                },
                {"role": "user", "content": text},
            ])
        return self._generate_text(extract_ai)

    def evaluate_relevance(self, title: str) -> str:
        evaluate_ai = self._generate_ai([
                {
                    "role": "system",
                    "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
                },
                {"role": "user", "content": title},
            ])
        
        return self._generate_text(evaluate_ai)

    def generate_summary(self, content: str) -> str:
        summarize_ai = self._generate_ai([
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "user", "content": content},
            ])
        
        return self._generate_text(summarize_ai)