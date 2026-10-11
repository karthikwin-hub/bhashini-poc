"""Pure domain logic for user session state machine and language selection."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SessionState(str, Enum):
    """Lifecycle states of a WhatsApp user interaction session."""

    IDLE = "IDLE"
    AWAITING_LANGUAGES = "AWAITING_LANGUAGES"
    AWAITING_MENU = "AWAITING_MENU"
    AWAITING_TRANSLATE_INPUT = "AWAITING_TRANSLATE_INPUT"
    AWAITING_VOICE_MESSAGE = "AWAITING_VOICE_MESSAGE"
    AWAITING_WEATHER_LOCATION = "AWAITING_WEATHER_LOCATION"


SUPPORTED_LANGUAGES: dict[str, str] = {
    "1": "en",  # English
    "2": "hi",  # Hindi
    "3": "te",  # Telugu
    "4": "bn",  # Bengali
    "5": "ta",  # Tamil
    "6": "gom",  # Konkani (Goan Konkani code in Bhashini)
}

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "te": "Telugu (తెలుగు)",
    "bn": "Bengali (বাংলা)",
    "ta": "Tamil (தமிழ்)",
    "gom": "Konkani (कोंकणी)",
}

LANGUAGE_ALIAS_MAP: dict[str, str] = {
    "english": "en",
    "en": "en",
    "hindi": "hi",
    "hi": "hi",
    "telugu": "te",
    "te": "te",
    "bengali": "bn",
    "bn": "bn",
    "tamil": "ta",
    "ta": "ta",
    "konkani": "gom",
    "gom": "gom",
    "kok": "gom",
}


class LanguageValidator:
    """Validates and parses user language choices (up to 3 selections)."""

    @staticmethod
    def parse_selection(user_input: str) -> tuple[list[str], str | None]:
        """Parse comma or space separated language codes/indices.

        Returns (selected_codes, error_message).
        """
        if not user_input or not user_input.strip():
            return [], "Please select up to 3 languages (e.g. 1, 2)."

        raw_tokens = [t.strip().lower() for t in user_input.replace(",", " ").split() if t.strip()]
        selected: list[str] = []

        for token in raw_tokens:
            if token in SUPPORTED_LANGUAGES:
                code = SUPPORTED_LANGUAGES[token]
                if code not in selected:
                    selected.append(code)
            elif token in LANGUAGE_ALIAS_MAP:
                code = LANGUAGE_ALIAS_MAP[token]
                if code not in selected:
                    selected.append(code)
            else:
                # Unrecognized token
                pass

        if len(selected) > 3:
            return [], "Please select a maximum of 3 languages (e.g. 1, 2)."

        if not selected:
            return (
                [],
                "Please select valid options (1-6) or language names. Select up to 3 languages.",
            )

        return selected, None


@dataclass
class UserSession:
    """User session model tracking conversation state and preferences."""

    phone_number: str
    state: SessionState = SessionState.IDLE
    selected_languages: list[str] = field(default_factory=list)
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class UserSessionManager:
    """Manages conversational state machine and orchestrates user interactions."""

    def __init__(
        self,
        bhashini_client: Any = None,
        whatsapp_client: Any = None,
        weather_client: Any = None,
    ) -> None:
        self._sessions: dict[str, UserSession] = {}
        self.bhashini_client = bhashini_client
        self.whatsapp_client = whatsapp_client
        self.weather_client = weather_client

    def get_or_create_session(self, phone: str) -> UserSession:
        """Retrieve existing session or create an IDLE session."""
        if phone not in self._sessions:
            self._sessions[phone] = UserSession(phone_number=phone, state=SessionState.IDLE)
        return self._sessions[phone]

    def get_session(self, phone: str) -> UserSession:
        """Retrieve existing session."""
        return self.get_or_create_session(phone)

    def reset_session(self, phone: str) -> UserSession:
        """Reset session back to IDLE state."""
        session = self.get_or_create_session(phone)
        session.state = SessionState.IDLE
        session.selected_languages = []
        return session

    def handle_user_input(self, phone: str, message_text: str | None = None) -> str:
        """Advance session state machine based on text input and return prompt."""
        session = self.get_or_create_session(phone)
        text = (message_text or "").strip()

        # Handle global resets
        if text.lower() in ("reset", "restart", "start again"):
            self.reset_session(phone)
            session.state = SessionState.AWAITING_LANGUAGES
            return self._format_language_prompt()

        if session.state == SessionState.IDLE:
            # Any initial greeting triggers language selection prompt
            session.state = SessionState.AWAITING_LANGUAGES
            return self._format_language_prompt()

        if session.state == SessionState.AWAITING_LANGUAGES:
            selected, error = LanguageValidator.parse_selection(text)
            if error:
                return error
            session.selected_languages = selected
            session.state = SessionState.AWAITING_MENU
            return self._format_main_menu(selected)

        if session.state == SessionState.AWAITING_MENU:
            if text.startswith("1") or "translate" in text.lower() or "अनुवाद" in text:
                session.state = SessionState.AWAITING_TRANSLATE_INPUT
                return (
                    "Translate mode selected. Please send text, upload a document (.txt), "
                    "or send a voice clip."
                )
            if text.startswith("2") or "voice" in text.lower() or "आवाज़" in text:
                session.state = SessionState.AWAITING_VOICE_MESSAGE
                return (
                    "Voice Message mode selected. "
                    "Please speak into WhatsApp and send your voice note."
                )
            if text.startswith("3") or "weather" in text.lower() or "मौसम" in text:
                session.state = SessionState.AWAITING_WEATHER_LOCATION
                return (
                    "Weather mode selected. Please share your GPS location pin or type a city name."
                )

            return "Please choose an option from the menu:\n" + self._format_main_menu(
                session.selected_languages
            )

        return "Please send your input for the selected mode, or type 'reset' to change settings."

    def _format_language_prompt(self) -> str:
        return (
            "Welcome to Bhashini Sovereign Multilingual Assistant! / "
            "भाषिणी बहुभाषी सहायक में आपका स्वागत है!\n\n"
            "Please select up to 3 languages by number (e.g., 1, 2):\n"
            "1. English\n"
            "2. Hindi\n"
            "3. Telugu\n"
            "4. Bengali\n"
            "5. Tamil\n"
            "6. Konkani"
        )

    def _format_main_menu(self, languages: list[str]) -> str:
        return (
            "Main Menu / मुख्य मेनू:\n"
            "1. Translate / अनुवाद (Text, Document, Audio)\n"
            "2. Voice Message / आवाज़ (Speak & listen in your languages)\n"
            "3. Weather / मौसम (Current & 2-day forecast)"
        )

    async def process_translate_input(
        self,
        phone: str,
        input_type: str,
        content: str | None = None,
        audio_bytes: bytes | None = None,
    ) -> list[str]:
        """Translate input text, document, or audio into user's chosen languages."""
        session = self.get_or_create_session(phone)
        targets = session.selected_languages or ["en", "hi"]

        if input_type not in ("text", "document", "audio"):
            return [
                "Unsupported input format. "
                "Please send text, a text document, or an audio voice note."
            ]

        text_to_translate = content or ""
        if input_type == "audio":
            if self.bhashini_client and hasattr(self.bhashini_client, "transcribe_audio"):
                text_to_translate = await self.bhashini_client.transcribe_audio(
                    audio_bytes or b"", source_lang="hi"
                )
            else:
                text_to_translate = "Audio input"

        if not text_to_translate:
            return ["Could not extract text from the provided input."]

        results: list[str] = []
        for tgt in targets:
            if self.bhashini_client and hasattr(self.bhashini_client, "translate_text"):
                translated = await self.bhashini_client.translate_text(
                    text_to_translate, src="auto", target=tgt
                )
                results.append(translated)
            else:
                results.append(f"[{tgt} translation of {text_to_translate}]")

        return results

    async def process_voice_interaction(
        self,
        phone: str,
        audio_bytes: bytes,
    ) -> list[dict[str, Any]]:
        """Process voice note via ASR, multilingual NMT, and TTS synthesis."""
        session = self.get_or_create_session(phone)
        targets = session.selected_languages or ["hi"]

        if not audio_bytes:
            return [{"text": "माफ़ कीजिए, कोई आवाज़ नहीं सुनाई दी। कृपया दोबारा बोलें।"}]

        try:
            if not self.bhashini_client or not hasattr(self.bhashini_client, "transcribe_audio"):
                return [{"text": "Speech recognition service not configured."}]

            transcript = await self.bhashini_client.transcribe_audio(audio_bytes, source_lang="hi")
            if not transcript or not transcript.strip():
                return [{"text": "माफ़ कीजिए, कोई आवाज़ नहीं सुनाई दी। कृपया दोबारा बोलें।"}]

            results: list[dict[str, Any]] = []
            for tgt in targets:
                if hasattr(self.bhashini_client, "translate_and_tts"):
                    (
                        translated_text,
                        synthesized_audio,
                    ) = await self.bhashini_client.translate_and_tts(
                        transcript, src="hi", target=tgt
                    )
                    results.append({"text": translated_text, "audio_bytes": synthesized_audio})
                else:
                    results.append(
                        {"text": f"[{tgt}: {transcript}]", "audio_bytes": b"RIFF_SAMPLE"}
                    )

            return results
        except Exception:
            return [{"text": "माफ़ कीजिए, आपकी आवाज़ समझ नहीं आई। कृपया दोबारा बोलें।"}]

    async def process_weather_location(
        self,
        phone: str,
        latitude: float | None = None,
        longitude: float | None = None,
        location_text: str | None = None,
    ) -> list[str]:
        """Fetch weather advisory and translate into user's chosen languages."""
        session = self.get_or_create_session(phone)
        targets = session.selected_languages or ["en", "hi"]

        if not self.weather_client:
            return ["Weather service not configured."]

        try:
            if latitude is not None and longitude is not None:
                summary = await self.weather_client.get_forecast_by_coords(latitude, longitude)
            elif location_text:
                summary = await self.weather_client.get_forecast_by_city(location_text)
            else:
                return ["Please share your GPS location pin or type a city name."]
        except Exception:
            return [
                "Location not found / शहर नहीं मिला. "
                "Please share a valid city name or GPS location pin."
            ]

        results: list[str] = []
        for tgt in targets:
            if self.bhashini_client and hasattr(self.bhashini_client, "translate_text"):
                translated = await self.bhashini_client.translate_text(
                    summary, src="en", target=tgt
                )
                results.append(translated)
            else:
                results.append(f"[{tgt} Weather: {summary}]")

        return results
