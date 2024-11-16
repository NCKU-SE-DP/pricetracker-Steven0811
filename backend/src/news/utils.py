import itertools
from openai import OpenAI
from src.news.constants import ID_COUNTER_START
from src.config import AI

class NewsUtils(AI):
    def __init__(self):
        super().__init__()
        self._id_counter = itertools.count(start=ID_COUNTER_START)

    def generate_ai(self, message):
        ai = OpenAI(api_key="xxx").chat.completions.create(
            model = self.AI_MODEL,
            messages = message,
        )
        return ai
