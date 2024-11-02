import itertools
from openai import OpenAI
from src.news.constants import ID_COUNTER_START

_id_counter = itertools.count(start=ID_COUNTER_START)

def generate_ai(message):
    ai = OpenAI(api_key="xxx").chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = message,
    )
    return ai
