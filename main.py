"""Entry point for the Vocabulary Builder Telegram bot."""

import asyncio
import logging

from src.bot import VocabularyBot
from src.config import Settings


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def main() -> None:
    """Initialize and run the bot."""
    setup_logging()
    settings = Settings()
    bot = VocabularyBot(settings)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
