from typing import Annotated, List, Literal

from annotated_types import Ge, Le, MaxLen, MinLen
from pydantic import BaseModel, Field

# Type alias for language
Language = Literal["english", "german"]


class UsageExample(BaseModel):
    """Schema for a usage example of a word or a phrase."""

    meaning: str = Field(
        ..., description="Explain this meaning of the word/phrase in the usage example"
    )
    example: str = Field(
        ..., description="Usage example of the word/phrase in the real context"
    )
    task_sentence: str = Field(
        ...,
        description="The example sentence with '_____' instead of the word/phrase",
    )
    answer_keyword: str = Field(
        ...,
        description="The fragment that needs to be inserted into the gap",
    )


class Card(BaseModel):
    """Schema for a card with a new word or a phrase and its usage examples for Quizlet."""

    reasoning: str = Field(
        ...,
        description="Short reasoning about the word/phrase, its meaning, usage example and context, etc. Can this word be used in different meanings? Are they truly distinct (homonyms) or just slight nuances? explicitly state: 'I will create X cards because...",
    )
    amount_of_meanings: Annotated[int, Ge(1), Le(3)] = Field(
        ..., description="Amount of useful meanings of the word/phrase, maximum 3"
    )
    usage_examples: Annotated[List[UsageExample], MinLen(1), MaxLen(3)] = Field(
        ...,
        description="List of usage examples of the word/phrase in the real context for each meaning",
    )
