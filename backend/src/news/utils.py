import itertools
from openai import OpenAI
from src.news.constants import ID_COUNTER_START
from src.config import AI

_id_counter = itertools.count(start=ID_COUNTER_START)

def generate_ai(message):
    ai = OpenAI(api_key="xxx").chat.completions.create(
        model = AI.AI_MODEL,
        messages = message,
    )
    return ai
