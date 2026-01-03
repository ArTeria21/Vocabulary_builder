"""Telegram bot for vocabulary building using Contextual Immersion method."""

import logging
from dataclasses import dataclass, field
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.build_card import CardBuildError, build_card
from src.card_manager import CardManager, WordHistoryEntry
from src.config import Settings
from src.schemas import Card, Language

logger = logging.getLogger(__name__)

# Telegram message length limit
MAX_MESSAGE_LENGTH = 4096
SAFE_MESSAGE_LENGTH = 3800  # Leave some buffer for emojis and formatting

router = Router()


@dataclass
class PendingCard:
    """Card awaiting user action (accept/decline/regenerate)."""

    word_identifier: str
    card: Card
    language: Language
    chat_id: int
    message_id: int
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_duplicate: bool = False
    duplicate_entry: WordHistoryEntry | None = None


class VocabularyBot:
    """
    Telegram bot for creating Quizlet vocabulary cards.

    Uses the Contextual Immersion method:
    - Term: The word/phrase itself
    - Definition: Definition + Collocations + Gap-fill examples (all in target language)
    - No translations to Russian/native language
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the bot.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN.get_secret_value())
        self.dp = Dispatcher()
        self.card_manager = CardManager(
            english_path=settings.ENGLISH_CSV_PATH,
            german_path=settings.GERMAN_CSV_PATH,
        )

        # Store pending cards awaiting user action (keyed by message_id)
        self._pending_cards: dict[int, PendingCard] = {}

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

        # Register callback handlers for inline buttons
        self.dp.callback_query.register(
            self._handle_accept, F.data.startswith("accept:")
        )
        self.dp.callback_query.register(
            self._handle_decline, F.data.startswith("decline:")
        )
        self.dp.callback_query.register(
            self._handle_regenerate, F.data.startswith("regenerate:")
        )

    def _build_card_keyboard(self, message_id: int) -> InlineKeyboardMarkup:
        """
        Build inline keyboard for card actions.

        Args:
            message_id: The message ID to use in callbacks.

        Returns:
            Inline keyboard with accept, decline, and regenerate buttons.
        """
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="✅ Accept", callback_data=f"accept:{message_id}"),
            InlineKeyboardButton(text="❌ Decline", callback_data=f"decline:{message_id}"),
            InlineKeyboardButton(text="🔄 Regenerate", callback_data=f"regenerate:{message_id}"),
        )
        builder.adjust(3)
        return builder.as_markup()

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
            "**Methodology: Contextual Immersion**\n"
            "I create Quizlet flashcards using definitions, collocations, "
            "and gap-fill examples — all in the target language. "
            "No translations to Russian!\n\n"
            "**Usage:**\n"
            "• `/en useful` — for English words\n"
            "• `/de aufgeben` — for German words\n\n"
            "**Card Format:**\n"
            "*Side 1 (Term):* The word/phrase\n"
            "*Side 2 (Definition):* Definition + Collocations + Gap-fill examples\n\n"
            "**Commands:**\n"
            "/dump_english — Get English cards (.txt) and clear buffer\n"
            "/dump_german — Get German cards (.txt) and clear buffer\n"
            "/stats — View current statistics",
            parse_mode="Markdown",
        )

    async def _handle_dump_english(self, message: Message) -> None:
        """Handle /dump_english command - send .txt file and clear buffer."""
        if not await self._check_user(message):
            return

        if not self.card_manager.has_cards("english"):
            await message.answer("📭 No English cards in the buffer yet.")
            return

        txt_path = self.card_manager.dump_txt("english")
        if txt_path:
            await message.answer_document(
                FSInputFile(txt_path, filename="english_vocabulary.txt"),
                caption="📥 Here are your English cards! Ready for Quizlet Custom Import. Buffer cleared.",
            )

    async def _handle_dump_german(self, message: Message) -> None:
        """Handle /dump_german command - send .txt file and clear buffer."""
        if not await self._check_user(message):
            return

        if not self.card_manager.has_cards("german"):
            await message.answer("📭 No German cards in the buffer yet.")
            return

        txt_path = self.card_manager.dump_txt("german")
        if txt_path:
            await message.answer_document(
                FSInputFile(txt_path, filename="german_vocabulary.txt"),
                caption="📥 Here are your German cards! Ready for Quizlet Custom Import. Buffer cleared.",
            )

    async def _handle_stats(self, message: Message) -> None:
        """Handle /stats command - show current statistics."""
        if not await self._check_user(message):
            return

        stats = self.card_manager.get_stats()
        history_stats = self.card_manager.get_history_stats()

        await message.answer(
            "📊 Current Statistics\n\n"
            f"🇬🇧 English:\n"
            f"   • Cards in buffer: {stats['english'].cards_count}\n"
            f"   • Unique words (session): {stats['english'].unique_words}\n"
            f"   • Total in history: {history_stats['english']}\n\n"
            f"🇩🇪 German:\n"
            f"   • Cards in buffer: {stats['german'].cards_count}\n"
            f"   • Unique words (session): {stats['german'].unique_words}\n"
            f"   • Total in history: {history_stats['german']}"
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

    async def _send_long_message(
        self, chat_id: int, text: str, message: Message | None = None
    ) -> None:
        """
        Send a long message by splitting it into multiple parts if needed.

        Args:
            chat_id: The chat ID to send the message to.
            text: The text to send.
            message: If provided, edit this message instead of sending new ones.
        """
        if len(text) <= SAFE_MESSAGE_LENGTH:
            if message:
                await message.edit_text(text)
            else:
                await self.bot.send_message(chat_id, text)
            return

        # Split message into chunks
        chunks = []
        remaining_text = text

        while remaining_text:
            # Try to find a good split point (newline)
            chunk = remaining_text[:SAFE_MESSAGE_LENGTH]

            if len(remaining_text) > SAFE_MESSAGE_LENGTH:
                # Find last newline within the chunk
                last_newline = chunk.rfind("\n")
                if last_newline > SAFE_MESSAGE_LENGTH * 0.7:
                    chunk = chunk[:last_newline]
                    remaining_text = remaining_text[last_newline + 1:]
                else:
                    remaining_text = remaining_text[SAFE_MESSAGE_LENGTH:]
            else:
                remaining_text = ""

            chunks.append(chunk)

        # Send chunks
        for i, chunk in enumerate(chunks):
            if i == 0 and message:
                await message.edit_text(chunk)
            else:
                await self.bot.send_message(chat_id, chunk)

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

        # Use full input as identifier (preserves context like "bank (river)")
        word_identifier = command.args
        word = word.strip()

        # Check for duplicate in history using full input as key
        is_duplicate, duplicate_entry = self.card_manager.has_duplicate(
            word_identifier, language
        )

        if is_duplicate:
            duplicate_warning = (
                f"⚠️ This word was already added before!\n\n"
                f"Previous definition: {duplicate_entry.definition}\n\n"
                f"Added on: {duplicate_entry.added_at[:10]}\n\n"
                f"Continuing anyway..."
            )
            # Send warning, then continue with processing
            await message.answer(duplicate_warning)

        # Send processing message
        processing_msg = await message.answer("🔄 Processing your word...")

        try:
            # Build the card using LLM (includes retry logic)
            card = await build_card(word, language, self.settings)

            # Check if word exists
            if not card.is_exists:
                await self._send_long_message(
                    message.chat.id,
                    f'❌ Word not found: "{word_identifier}"\n\n'
                    f"This word does not exist in {language.capitalize()}, "
                    f"or it may be a typo, made-up word, or gibberish.",
                    message=processing_msg,
                )
                return

            # Store as pending card
            pending = PendingCard(
                word_identifier=word_identifier,
                card=card,
                language=language,
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                is_duplicate=is_duplicate,
                duplicate_entry=duplicate_entry,
            )
            self._pending_cards[processing_msg.message_id] = pending

            # Format response
            language_emoji = "🇬🇧" if language == "english" else "🇩🇪"
            language_name = language.capitalize()

            duplicate_notice = "⚠️ (duplicate) " if is_duplicate else ""

            response = (
                f'⚡️ Term: "{word_identifier}" {duplicate_notice}\n\n'
                f"📝 Definition:\n{card.definition}\n\n"
                f"🔗 Collocations:\n"
                + "\n".join(f"• {c}" for c in card.collocations)
                + "\n\n"
                f"📚 Examples:\n"
                + "\n".join(f"• {e}" for e in card.examples)
            )

            # Update message with card content and inline buttons
            await self._send_long_message(
                message.chat.id,
                response,
                message=processing_msg,
            )
            await self.bot.edit_message_reply_markup(
                chat_id=processing_msg.chat.id,
                message_id=processing_msg.message_id,
                reply_markup=self._build_card_keyboard(processing_msg.message_id),
            )

        except CardBuildError as e:
            logger.error("Card build failed for word '%s': %s", word[:50], e.message)
            error_text = (
                f"❌ Failed to create card after 3 attempts.\n\n"
                f"Word: {word[:100]}{'...' if len(word) > 100 else ''}\n"
                f"Error: {e.message[:300]}"
            )
            await self._send_long_message(
                message.chat.id, error_text, message=processing_msg
            )

        except Exception as e:
            logger.exception("Unexpected error processing word: %s", word[:50])
            error_text = (
                f"❌ Unexpected error occurred.\n\n"
                f"Please try again later or contact support.\n"
                f"Details: {type(e).__name__}: {str(e)[:200]}"
            )
            await self._send_long_message(
                message.chat.id, error_text, message=processing_msg
            )

    async def _handle_accept(self, callback: CallbackQuery) -> None:
        """Handle Accept button - add card to buffer."""
        await callback.answer()

        if callback.from_user.id != self.settings.ALLOWED_USER_ID:
            await callback.message.answer("⛔ Sorry, this bot is private.")
            return

        # Extract message_id from callback data
        try:
            message_id = int(callback.data.split(":")[1])
        except (IndexError, ValueError):
            logger.error("Invalid callback data: %s", callback.data)
            return

        pending = self._pending_cards.get(message_id)
        if not pending:
            await callback.message.edit_text("❌ This card is no longer available.")
            return

        # Add card to manager
        cards_added = self.card_manager.add_card(
            pending.word_identifier, pending.card, pending.language
        )

        language_emoji = "🇬🇧" if pending.language == "english" else "🇩🇪"
        language_name = pending.language.capitalize()

        await callback.message.edit_text(
            f'✅ Card accepted: "{pending.word_identifier}"\n\n'
            f"Added {cards_added} card for {language_name} {language_emoji}"
        )

        # Remove from pending
        del self._pending_cards[message_id]

    async def _handle_decline(self, callback: CallbackQuery) -> None:
        """Handle Decline button - discard the card."""
        await callback.answer()

        if callback.from_user.id != self.settings.ALLOWED_USER_ID:
            await callback.message.answer("⛔ Sorry, this bot is private.")
            return

        # Extract message_id from callback data
        try:
            message_id = int(callback.data.split(":")[1])
        except (IndexError, ValueError):
            logger.error("Invalid callback data: %s", callback.data)
            return

        pending = self._pending_cards.get(message_id)
        if not pending:
            await callback.message.edit_text("❌ This card is no longer available.")
            return

        await callback.message.edit_text(
            f'❌ Card declined: "{pending.word_identifier}"\n\n'
            "The card was not added to your buffer."
        )

        # Remove from pending
        del self._pending_cards[message_id]

    async def _handle_regenerate(self, callback: CallbackQuery) -> None:
        """Handle Regenerate button - generate a new card for the same word."""
        await callback.answer("🔄 Regenerating...")

        if callback.from_user.id != self.settings.ALLOWED_USER_ID:
            await callback.message.answer("⛔ Sorry, this bot is private.")
            return

        # Extract message_id from callback data
        try:
            message_id = int(callback.data.split(":")[1])
        except (IndexError, ValueError):
            logger.error("Invalid callback data: %s", callback.data)
            return

        pending = self._pending_cards.get(message_id)
        if not pending:
            await callback.message.edit_text("❌ This card is no longer available.")
            return

        word = pending.word_identifier.strip()

        try:
            # Build new card using LLM
            new_card = await build_card(word, pending.language, self.settings)

            # Update pending card with new content
            pending.card = new_card

            # Format response
            duplicate_notice = "⚠️ (duplicate) " if pending.is_duplicate else ""

            response = (
                f'⚡️ Term: "{pending.word_identifier}" {duplicate_notice}\n\n'
                f"📝 Definition:\n{new_card.definition}\n\n"
                f"🔗 Collocations:\n"
                + "\n".join(f"• {c}" for c in new_card.collocations)
                + "\n\n"
                f"📚 Examples:\n"
                + "\n".join(f"• {e}" for e in new_card.examples)
                + "\n\n"
                "🔄 Regenerated"
            )

            await self._send_long_message(
                callback.message.chat.id, response, message=callback.message
            )
            await self.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=self._build_card_keyboard(callback.message.message_id),
            )

        except CardBuildError as e:
            logger.error("Card build failed for word '%s': %s", word[:50], e.message)
            error_text = (
                f"❌ Failed to regenerate card after 3 attempts.\n\n"
                f"Word: {word[:100]}{'...' if len(word) > 100 else ''}\n"
                f"Error: {e.message[:300]}"
            )
            await callback.message.edit_text(error_text)
            # Remove from pending as regeneration failed
            del self._pending_cards[message_id]

        except Exception as e:
            logger.exception("Unexpected error regenerating word: %s", word[:50])
            error_text = (
                f"❌ Unexpected error occurred during regeneration.\n\n"
                f"Details: {type(e).__name__}: {str(e)[:200]}"
            )
            await callback.message.edit_text(error_text)
            # Remove from pending as regeneration failed
            del self._pending_cards[message_id]

    async def run(self) -> None:
        """Start the bot polling."""
        logger.info("Starting Vocabulary Builder Bot...")
        await self.dp.start_polling(self.bot)
