from typing import Annotated, List, Literal

from annotated_types import Ge, Le, MaxLen, MinLen
from pydantic import BaseModel, Field


class UsageExample(BaseModel):
    """Schema for a usage example of a word or a phrase"""

    meaning: str = Field(
        ..., description="Explain this meaning of the word/phrase in the usage example"
    )
    example: str = Field(
        ..., description="Usage example of the word/phrase in the real context"
    )
    task: str = Field(
        ...,
        description="It should be the same example, but with '_____' instead of the word/phrase",
    )
    answer: str = Field(
        ...,
        description="The fragment that needs to be inserted into the gap",
    )


class Card(BaseModel):
    """Schema for a card with a new word or a phrase and it's usage example for the Quizlet"""

    language: Literal["english", "german"] = Field(
        ..., description="The language of the word/phrase"
    )
    reasoning: str = Field(
        ...,
        description="Short reasoning about the word/phrase, it's meaning, usage example and context, etc. Can this word be used in different meanings?",
    )
    amount_of_meanings: Annotated[int, Ge(1), Le(3)] = Field(
        ..., description="Amount of useful meanings of the word/phrase, maximum 5"
    )
    usage_examples: Annotated[List[UsageExample], MinLen(1), MaxLen(3)] = Field(
        ...,
        description="List of usage examples of the word/phrase in the real context for each meaning",
    )
