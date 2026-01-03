from typing import Annotated, List, Literal

from annotated_types import Ge, Le, MaxLen, MinLen
from pydantic import BaseModel, Field, field_validator

# Type alias for language
Language = Literal["english", "german"]


class Card(BaseModel):
    """
    Schema for a Quizlet card using Contextual Immersion method.

    Structure:
    - is_exists: Whether the word exists in the target language
    - normalized_term: The normalized (lemmatized) form of the word for saving to the card
    - definition, collocations, examples: Only populated if is_exists=True
    """

    is_exists: bool = Field(
        ...,
        description="Whether this word/phrase exists in the target language. Set to false for non-existent words, typos, or gibberish.",
    )
    normalized_term: str | None = Field(
        default=None,
        description=(
            "The normalized (lemmatized) form of the word/phrase to be used as the term in the card. "
            "For English: verbs in infinitive, nouns in singular form, etc. "
            "For German: verbs in infinitive, nouns with article (der/die/das), etc. "
            "Only populated if is_exists=True."
        ),
    )
    definition: str | None = Field(
        default=None,
        description="Clear, simple definition in the target language with synonyms in parentheses. Only populated if is_exists=True. Example: 'adj. Not able to make decisions quickly and effectively. (Syn: hesitant, unsure)'",
    )
    collocations: Annotated[List[str], MinLen(2), MaxLen(3)] | None = Field(
        default=None,
        description="2-3 common collocations/phrases containing the word. Each should have a gap: 'a weak and _____ man', 'proved to be _____'. Only populated if is_exists=True.",
    )
    examples: Annotated[List[str], MinLen(2), MaxLen(3)] | None = Field(
        default=None,
        description="2-3 example sentences where the target word is replaced by '_____'. Example: 'He was too _____ to carry out his political program.' Only populated if is_exists=True.",
    )

    @field_validator("normalized_term", "definition", "collocations", "examples", mode="after")
    @classmethod
    def validate_card_fields(cls, v: str | List[str] | None, info) -> str | List[str] | None:
        """If is_exists is True, all fields must be populated. If False, all must be None."""
        if info.data.get("is_exists"):
            if v is None:
                raise ValueError("Field must be populated when is_exists=True")
        else:
            if v is not None:
                raise ValueError("Field must be None when is_exists=False")
        return v
