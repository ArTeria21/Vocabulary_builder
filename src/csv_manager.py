"""CSV storage manager for vocabulary cards."""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.schemas import Card, Language


@dataclass
class Stats:
    """Statistics for a language buffer."""

    cards_count: int = 0
    unique_words: int = 0


@dataclass
class CSVManager:
    """
    Manages CSV storage for vocabulary cards.

    Handles storing cards, dumping CSV files, and tracking statistics.
    """

    english_path: str
    german_path: str
    _english_cards: list[tuple[str, str]] = field(default_factory=list)
    _german_cards: list[tuple[str, str]] = field(default_factory=list)
    _english_unique_words: int = 0
    _german_unique_words: int = 0

    def __post_init__(self) -> None:
        """Ensure data directories exist."""
        Path(self.english_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.german_path).parent.mkdir(parents=True, exist_ok=True)

    def add_card(self, card: Card, language: Language) -> int:
        """
        Add a card to the specified language buffer.

        Args:
            card: The vocabulary card to add.
            language: The language buffer to add to ('english' or 'german').

        Returns:
            Number of usage examples (cards) added.
        """
        cards_list = (
            self._english_cards if language == "english" else self._german_cards
        )

        for example in card.usage_examples:
            # Task sentence already contains hint from LLM
            cards_list.append((example.task_sentence, example.answer_keyword))

        # Track unique words (1 request = 1 unique word)
        if language == "english":
            self._english_unique_words += 1
        else:
            self._german_unique_words += 1

        return len(card.usage_examples)

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

    def dump_csv(self, language: Language) -> str | None:
        """
        Dump cards to CSV file and clear the buffer.

        Args:
            language: Which language buffer to dump.

        Returns:
            Path to the CSV file, or None if buffer was empty.
        """
        if language == "english":
            cards = self._english_cards
            path = self.english_path
        else:
            cards = self._german_cards
            path = self.german_path

        if not cards:
            return None

        # Create DataFrame without headers/index, tab-separated, no quotes
        df = pd.DataFrame(cards)
        df.to_csv(
            path, index=False, header=False, sep="\t", quoting=3
        )  # quoting=3 = QUOTE_NONE

        # Clear the buffer and reset unique words counter
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
