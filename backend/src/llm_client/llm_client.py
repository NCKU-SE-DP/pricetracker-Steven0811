import aisuite as ai
from src.llm_client.base import LLMClientTemplate
from src.llm_client.config import OpenAIConfig, AnthropicConfig

class OpenAIClient(LLMClientTemplate):
    def _initialize_client(self):
        try:
            self.client = ai.Client({"openai": {"api_key": self._api_key}})
            self.model = OpenAIConfig.model
            
        except Exception as error:
            raise ValueError(f"[OpenAIClient] Initialization failed: {error}")

class AnthropicAIClient(LLMClientTemplate):
    def _initialize_client(self):
        try:
            self.client = ai.Client({"anthropic": {"api_key": self._api_key}})
            self.model = AnthropicConfig.model

        except Exception as error:
            raise ValueError(f"[AnthropicAIClient] Initialization failed: {error}")