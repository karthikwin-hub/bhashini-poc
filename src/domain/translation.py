"""Pure domain models for multilingual translation."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TranslationRequest:
    """Request to translate text into multiple target languages."""

    text: str
    source_language: str
    target_languages: list[str]


@dataclass(frozen=True)
class TranslationResponse:
    """Translation result for a single target language."""

    target_language: str
    translated_text: str


@dataclass(frozen=True)
class MultilingualTranslationResult:
    """Aggregated translation result across multiple target languages."""

    original_text: str
    source_language: str
    translations: dict[str, str] = field(default_factory=dict)
