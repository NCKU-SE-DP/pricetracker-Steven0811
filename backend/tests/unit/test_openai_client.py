import unittest
import os
from unittest.mock import patch
from src.llm_client.llm_client import OpenAIClient

# 除非確認要使用真實的API進行測試(當然會因此擁有額外的開銷)，否則將RUN_REAL_API_TESTS設置為False
RUN_REAL_API_TESTS = os.getenv("RUN_REAL_API_TESTS", "false").lower() == "true"


class TestOpenAIClient(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        if RUN_REAL_API_TESTS:
            self.client = OpenAIClient(_api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self.client = OpenAIClient(_api_key="fake_api_key")

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    def test_evaluate_relevance_real(self):
        result = self.client.evaluate_relevance("食品價格上漲")
        self.assertIn(result, ["high", "medium", "low"])

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    def test_generate_summary_real(self):
        result = self.client.generate_summary("一篇有關食品價格的新聞內容")
        self.assertIn("影響", result)
        self.assertIn("原因", result)

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    def test_extract_search_keywords_real(self):
        result = self.client.extract_search_keywords("這篇新聞提到食品價格的波動以及市場的供應鏈問題")
        self.assertGreater(len(result.split()), 0)
    
    @patch('src.llm_client.llm_client.OpenAIClient._generate_text')
    def test_evaluate_relevance(self, mock_generate_text):
        mock_generate_text.return_value = 'high'

        result = self.client.evaluate_relevance("食品價格上漲")

        self.assertEqual(result, 'high')

    @patch('src.llm_client.llm_client.OpenAIClient._generate_text')
    def test_generate_summary(self, mock_generate_text):
        mock_generate_text.return_value = '{"影響": "影響描述", "原因": "原因描述"}'

        result = self.client.generate_summary("一篇新聞內容")

        self.assertEqual(result, '{"影響": "影響描述", "原因": "原因描述"}')

    @patch('src.llm_client.llm_client.OpenAIClient._generate_text')
    def test_extract_search_keywords(self, mock_generate_text):
        mock_generate_text.return_value = '食品 價格'

        result = self.client.extract_search_keywords("一段希望看到的新聞文字")

        self.assertEqual(result, '食品 價格')


if __name__ == '__main__':
    unittest.main()