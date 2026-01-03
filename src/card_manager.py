"""Storage manager for vocabulary cards using Quizlet Custom Import format."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.schemas import Card, Language


@dataclass
class Stats:
    """Statistics for a language buffer."""

    cards_count: int = 0
    unique_words: int = 0


@dataclass
class WordHistoryEntry:
    """Entry in word history."""

    word: str
    added_at: str
    definition: str


@dataclass
class CardManager:
    """
    Manages storage for vocabulary cards in Quizlet Custom Import format.

    Format:
    - Card Separator: ####
    - Field Separator: Tab (\t)
    - Multi-line definitions are preserved

    Output file format (.txt):
    ```
    Term1	Definition with collocations and examples
    ####
    Term2	Definition with collocations and examples
    ####
    ```

    Also maintains a history of all words ever added for duplicate checking.
    """

    english_path: str
    german_path: str
    _english_cards: list[tuple[str, str]] = field(default_factory=list)
    _german_cards: list[tuple[str, str]] = field(default_factory=list)
    _english_unique_words: int = 0
    _german_unique_words: int = 0
    _english_history: dict[str, WordHistoryEntry] = field(default_factory=dict)
    _german_history: dict[str, WordHistoryEntry] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure data directories exist and load word history."""
        data_dir = Path(self.english_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)

        # Load word history from files
        self._load_history("english")
        self._load_history("german")

    def _get_history_path(self, language: Language) -> Path:
        """Get the path to the history file for the specified language."""
        data_dir = Path(self.english_path).parent
        return data_dir / f"{language}_history.json"

    def _load_history(self, language: Language) -> None:
        """
        Load word history from JSON file.

        Args:
            language: The language to load history for.
        """
        history_path = self._get_history_path(language)

        if not history_path.exists():
            return

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if language == "english":
                self._english_history = {
                    word: WordHistoryEntry(**entry)
                    for word, entry in data.items()
                }
            else:
                self._german_history = {
                    word: WordHistoryEntry(**entry)
                    for word, entry in data.items()
                }

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # If history file is corrupted, start fresh
            print(f"Warning: Failed to load {language} history: {e}")

    def _save_history(self, language: Language) -> None:
        """
        Save word history to JSON file.

        Args:
            language: The language to save history for.
        """
        history_path = self._get_history_path(language)

        if language == "english":
            history = self._english_history
        else:
            history = self._german_history

        # Convert to serializable format
        serializable_history = {
            word: {
                "word": entry.word,
                "added_at": entry.added_at,
                "definition": entry.definition,
            }
            for word, entry in history.items()
        }

        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(serializable_history, f, indent=2, ensure_ascii=False)

    def has_duplicate(
        self, word: str, language: Language
    ) -> tuple[bool, WordHistoryEntry | None]:
        """
        Check if a word already exists in the history.

        Args:
            word: The word to check.
            language: The language to check in.

        Returns:
            Tuple of (is_duplicate, history_entry). If no duplicate found,
            is_duplicate is False and history_entry is None.
        """
        # Normalize word for comparison (case-insensitive, strip whitespace)
        normalized_word = word.lower().strip()

        if language == "english":
            history = self._english_history
        else:
            history = self._german_history

        # Check for exact match
        for stored_word, entry in history.items():
            if stored_word.lower().strip() == normalized_word:
                return True, entry

        return False, None

    def _format_definition(self, card: Card) -> str:
        """
        Format the card's definition with collocations and examples.

        Format:
        ```
        Definition

        Collocations:
        - collocation1
        - collocation2

        Examples:
        - example1
        - example2
        ```
        """
        lines = [card.definition]

        if card.collocations:
            lines.append("")
            lines.append("Collocations:")
            for collocation in card.collocations:
                lines.append(f"- {collocation}")

        if card.examples:
            lines.append("")
            lines.append("Examples:")
            for example in card.examples:
                lines.append(f"- {example}")

        return "\n".join(lines)

    def add_card(self, term: str, card: Card, language: Language) -> int:
        """
        Add a card to the specified language buffer and update history.

        Args:
            term: The target word/phrase (Side 1 of the card).
            card: The Card object with definition, collocations, and examples.
            language: The language buffer to add to ('english' or 'german').

        Returns:
            Number of cards added (always 1 with new format).
        """
        cards_list = (
            self._english_cards if language == "english" else self._german_cards
        )

        definition = self._format_definition(card)
        cards_list.append((term, definition))

        # Add to history (always, even if it's a duplicate - for tracking)
        history_entry = WordHistoryEntry(
            word=term,
            added_at=datetime.now().isoformat(),
            definition=card.definition,
        )

        if language == "english":
            self._english_unique_words += 1
            self._english_history[term] = history_entry
            self._save_history("english")
        else:
            self._german_unique_words += 1
            self._german_history[term] = history_entry
            self._save_history("german")

        return 1

    def get_stats(self) -> dict[str, Stats]:
        """
        Get current statistics for both languages.

        Returns:
            Dictionary with stats for 'english' and 'german'.
        """
        return {
            "english": Stats(
                cards_count=len(self._english_cards),
                unique_words=self._english_unique_words,
            ),
            "german": Stats(
                cards_count=len(self._german_cards),
                unique_words=self._german_unique_words,
            ),
        }

    def get_history_stats(self) -> dict[str, int]:
        """
        Get total history statistics (all words ever added).

        Returns:
            Dictionary with total word counts for each language.
        """
        return {
            "english": len(self._english_history),
            "german": len(self._german_history),
        }

    def dump_txt(self, language: Language) -> str | None:
        """
        Dump cards to .txt file in Quizlet Custom Import format and clear the buffer.

        Args:
            language: Which language buffer to dump.

        Returns:
            Path to the .txt file, or None if buffer was empty.
        """
        if language == "english":
            cards = self._english_cards
            path = self.english_path
        else:
            cards = self._german_cards
            path = self.german_path

        if not cards:
            return None

        # Write in Quizlet Custom Import format
        with open(path, "w", encoding="utf-8") as f:
            for i, (term, definition) in enumerate(cards):
                # Write: Term<TAB>Definition
                f.write(f"{term}\t{definition}")
                # Add card separator after each card (but not after the last one)
                if i < len(cards) - 1:
                    f.write("\n####")

        # Clear the buffer but keep the counter for session tracking
        if language == "english":
            self._english_cards = []
            self._english_unique_words = 0
        else:
            self._german_cards = []
            self._german_unique_words = 0

        return path

    def has_cards(self, language: Language) -> bool:
        """Check if there are cards in the specified language buffer."""
        if language == "english":
            return len(self._english_cards) > 0
        return len(self._german_cards) > 0
