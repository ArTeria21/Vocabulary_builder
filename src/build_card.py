"""LLM-based card generation module using Contextual Immersion method."""

import asyncio
import logging
import pprint
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import ValidationError

from src.config import Settings
from src.schemas import Card, Language

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


class CardBuildError(Exception):
    """Custom exception for card building errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)


def load_system_prompt(language: Language) -> str:
    """
    Load the system prompt for the specified language.

    Args:
        language: The language to load prompt for ('english' or 'german').

    Returns:
        The system prompt content.
    """
    prompt_filename = (
        "english_prompt.md" if language == "english" else "german_prompt.md"
    )
    prompt_path = Path(__file__).parent.parent / "prompts" / prompt_filename
    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


async def build_card(word: str, language: Language, settings: Settings) -> Card:
    """
    Build a vocabulary card for the given word using LLM with retry logic.

    Uses the Contextual Immersion method:
    - No translations to Russian/native language
    - Definition, collocations, and examples all in the target language
    - Gap-fill examples for active recall

    Args:
        word: The word or phrase to create a card for.
        language: The language of the word ('english' or 'german').
        settings: Application settings with API credentials.

    Returns:
        Card object with definition, collocations, and gap-fill examples.

    Raises:
        CardBuildError: If all retry attempts fail.
    """
    client = AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY.get_secret_value(),
        base_url=settings.OPENROUTER_BASE_URL,
    )

    last_error: Exception | None = None
    system_prompt = load_system_prompt(language)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Attempt %d/%d for word: %s", attempt, MAX_RETRIES, word[:50])

            response = await client.beta.chat.completions.parse(
                model=settings.MODEL_ID,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": word},
                ],
                response_format=Card,
            )

            parsed = response.choices[0].message.parsed
            if parsed is None:
                raise CardBuildError("LLM returned empty response")

            logger.info("Successfully built card on attempt %d", attempt)
            return parsed

        except ValidationError as e:
            last_error = e
            logger.warning(
                "Pydantic validation error on attempt %d: %s",
                attempt,
                str(e)[:200],
            )

        except APITimeoutError as e:
            last_error = e
            logger.warning("API timeout on attempt %d: %s", attempt, str(e)[:200])

        except APIConnectionError as e:
            last_error = e
            logger.warning(
                "API connection error on attempt %d: %s", attempt, str(e)[:200]
            )

        except APIStatusError as e:
            last_error = e
            logger.warning(
                "API status error on attempt %d (status %d): %s",
                attempt,
                e.status_code,
                str(e)[:200],
            )
            # Don't retry on 4xx client errors (except 429 rate limit)
            if 400 <= e.status_code < 500 and e.status_code != 429:
                break

        except Exception as e:
            last_error = e
            logger.warning("Unexpected error on attempt %d: %s", attempt, str(e)[:200])

        # Wait before retrying (except on last attempt)
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)

    # All retries exhausted
    error_type = type(last_error).__name__ if last_error else "Unknown"
    error_msg = str(last_error)[:300] if last_error else "No error details"

    raise CardBuildError(
        f"Failed after {MAX_RETRIES} attempts. Last error ({error_type}): {error_msg}",
        original_error=last_error,
    )


if __name__ == "__main__":

    async def main() -> None:
        result = await build_card(
            word="indecisive",
            language="english",
            settings=Settings(),
        )
        pprint.pprint(result.model_dump())
        print("-" * 100)
        print(result)

    asyncio.run(main())
