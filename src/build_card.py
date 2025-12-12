from src.config import Settings
from openai import OpenAI

from src.schemas import Card
import pprint

def load_system_prompt() -> str:
    with open("prompts/system_prompt.md", "r") as file:
        return file.read()

def build_card(word: str, settings: Settings) -> Card:
    client = OpenAI(api_key=settings.OPENROUTER_API_KEY.get_secret_value(), base_url=settings.OPENROUTER_BASE_URL)
    response = client.chat.completions.parse(
        model=settings.MODEL_ID,
        messages=[
            {"role": "system", "content": load_system_prompt()},
            {"role": "user", "content": f"Create a card with this word/phrase: {word}"}
        ],
        response_format=Card
    )
    return response.choices[0].message.parsed

if __name__ == "__main__":
    result = build_card("Разбери пожалуйста глагол Look, как фразовый глагол для экзамена FCE", Settings()).model_dump()
    pprint.pprint(result)
    print("-" * 100)
    print(result)