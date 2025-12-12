"""Telegram bot for vocabulary building."""

import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile, Message

from src.build_card import CardBuildError, build_card
from src.config import Settings
from src.csv_manager import CSVManager
from src.schemas import Language

logger = logging.getLogger(__name__)

router = Router()


class VocabularyBot:
    """Telegram bot for creating Quizlet vocabulary cards."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the bot.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN.get_secret_value())
        self.dp = Dispatcher()
        self.csv_manager = CSVManager(
            english_path=settings.ENGLISH_CSV_PATH,
            german_path=settings.GERMAN_CSV_PATH,
        )

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all message handlers."""
        self.dp.message.register(self._handle_start, Command("start"))
        self.dp.message.register(self._handle_dump_english, Command("dump_english"))
        self.dp.message.register(self._handle_dump_german, Command("dump_german"))
        self.dp.message.register(self._handle_stats, Command("stats"))
        self.dp.message.register(self._handle_english_word, Command("en"))
        self.dp.message.register(self._handle_german_word, Command("de"))
        self.dp.message.register(self._handle_unknown_text, F.text)

    async def _check_user(self, message: Message) -> bool:
        """Check if the user is allowed to use the bot."""
        if message.from_user.id != self.settings.ALLOWED_USER_ID:
            await message.answer("⛔ Sorry, this bot is private.")
            return False
        return True

    async def _handle_start(self, message: Message) -> None:
        """Handle /start command."""
        if not await self._check_user(message):
            return

        await message.answer(
            "👋 Welcome to the Vocabulary Builder Bot!\n\n"
            "Send me a word with language prefix:\n"
            "• `/en useful` — for English words\n"
            "• `/de aufgeben` — for German words\n\n"
            "📚 Commands:\n"
            "/dump_english — Get English cards CSV and clear buffer\n"
            "/dump_german — Get German cards CSV and clear buffer\n"
            "/stats — View current statistics",
            parse_mode="Markdown",
        )

    async def _handle_dump_english(self, message: Message) -> None:
        """Handle /dump_english command - send CSV and clear buffer."""
        if not await self._check_user(message):
            return

        if not self.csv_manager.has_cards("english"):
            await message.answer("📭 No English cards in the buffer yet.")
            return

        csv_path = self.csv_manager.dump_csv("english")
        if csv_path:
            await message.answer_document(
                FSInputFile(csv_path, filename="english_vocabulary.csv"),
                caption="📥 Here are your English cards! Buffer cleared.",
            )

    async def _handle_dump_german(self, message: Message) -> None:
        """Handle /dump_german command - send CSV and clear buffer."""
        if not await self._check_user(message):
            return

        if not self.csv_manager.has_cards("german"):
            await message.answer("📭 No German cards in the buffer yet.")
            return

        csv_path = self.csv_manager.dump_csv("german")
        if csv_path:
            await message.answer_document(
                FSInputFile(csv_path, filename="german_vocabulary.csv"),
                caption="📥 Here are your German cards! Buffer cleared.",
            )

    async def _handle_stats(self, message: Message) -> None:
        """Handle /stats command - show current statistics."""
        if not await self._check_user(message):
            return

        stats = self.csv_manager.get_stats()

        await message.answer(
            "📊 Current Statistics\n\n"
            f"🇬🇧 English:\n"
            f"   • Cards in buffer: {stats['english'].cards_count}\n"
            f"   • Unique words added: {stats['english'].unique_words}\n\n"
            f"🇩🇪 German:\n"
            f"   • Cards in buffer: {stats['german'].cards_count}\n"
            f"   • Unique words added: {stats['german'].unique_words}"
        )

    async def _handle_english_word(
        self, message: Message, command: CommandObject
    ) -> None:
        """Handle /en command - process English words."""
        if not await self._check_user(message):
            return
        await self._process_word(message, command, "english")

    async def _handle_german_word(
        self, message: Message, command: CommandObject
    ) -> None:
        """Handle /de command - process German words."""
        if not await self._check_user(message):
            return
        await self._process_word(message, command, "german")

    async def _handle_unknown_text(self, message: Message) -> None:
        """Handle plain text without command - prompt user to use /en or /de."""
        if not await self._check_user(message):
            return

        await message.answer(
            "❓ Please specify the language:\n"
            "• `/en word` — for English\n"
            "• `/de word` — for German",
            parse_mode="Markdown",
        )

    async def _process_word(
        self, message: Message, command: CommandObject, language: Language
    ) -> None:
        """Process a word for the specified language."""
        word = command.args
        if not word or not word.strip():
            await message.answer(
                f"❓ Please provide a word after the command.\n"
                f"Example: `/{command.command} {'useful' if language == 'english' else 'aufgeben'}`",
                parse_mode="Markdown",
            )
            return

        word = word.strip()

        # Send processing message
        processing_msg = await message.answer("🔄 Processing your word...")

        try:
            # Build the card using LLM (includes retry logic)
            card = await build_card(word, language, self.settings)

            # Add to CSV manager
            cards_added = self.csv_manager.add_card(card, language)

            # Format response
            language_emoji = "🇬🇧" if language == "english" else "🇩🇪"
            language_name = language.capitalize()

            response = f'⚡️ Word "{word.capitalize()}"\n\n'

            if cards_added == 1:
                response += f"Meaning:\n- {card.usage_examples[0].meaning}\n\n"
            else:
                response += f"👨🏼‍🎓 It has {cards_added} meanings:\n"
                for example in card.usage_examples:
                    response += f"- {example.meaning}\n"
                response += "\n"

            response += (
                f"✅ Added {cards_added} card(s) for {language_name} {language_emoji}"
            )

            await processing_msg.edit_text(response)

        except CardBuildError as e:
            logger.error("Card build failed for word '%s': %s", word[:50], e.message)
            await processing_msg.edit_text(
                f"❌ Failed to create card after 3 attempts.\n\n"
                f"Word: {word[:100]}{'...' if len(word) > 100 else ''}\n"
                f"Error: {e.message[:300]}"
            )

        except Exception as e:
            logger.exception("Unexpected error processing word: %s", word[:50])
            await processing_msg.edit_text(
                f"❌ Unexpected error occurred.\n\n"
                f"Please try again later or contact support.\n"
                f"Details: {type(e).__name__}: {str(e)[:200]}"
            )

    async def run(self) -> None:
        """Start the bot polling."""
        logger.info("Starting Vocabulary Builder Bot...")
        await self.dp.start_polling(self.bot)
