"""Interaction orchestrator and background worker for WhatsApp multilingual interactions."""

import logging
import uuid
from typing import Any

from src.adapters.audio.transcoder import AudioTranscoder
from src.adapters.bhashini.client import BhashiniPipelineClient
from src.adapters.weather.client import OpenMeteoClient
from src.adapters.whatsapp.client import WhatsAppClient
from src.api.config import get_settings
from src.domain.session import SessionState, UserSessionManager

logger = logging.getLogger(__name__)


class InteractionWorker:
    """Processes incoming WhatsApp messages and coordinates domain logic with client adapters."""

    def __init__(
        self,
        session_manager: UserSessionManager | None = None,
        bhashini_client: BhashiniPipelineClient | None = None,
        whatsapp_client: WhatsAppClient | None = None,
        weather_client: OpenMeteoClient | None = None,
        audio_transcoder: AudioTranscoder | None = None,
    ) -> None:
        settings = get_settings()
        self.bhashini_client = bhashini_client or BhashiniPipelineClient(
            user_id=settings.bhashini_user_id,
            api_key=settings.bhashini_api_key,
            pipeline_id=settings.bhashini_pipeline_id,
        )
        self.whatsapp_client = whatsapp_client or WhatsAppClient(
            token=settings.whatsapp_token,
            phone_number_id=settings.whatsapp_phone_number_id,
        )
        self.weather_client = weather_client or OpenMeteoClient()
        self.audio_transcoder = audio_transcoder or AudioTranscoder()
        self.session_manager = session_manager or UserSessionManager(
            bhashini_client=self.bhashini_client,
            whatsapp_client=self.whatsapp_client,
            weather_client=self.weather_client,
        )

    async def process_inbound_message(
        self,
        phone: str,
        message_data: dict[str, Any],
        correlation_id: str | None = None,
    ) -> list[str]:
        """Dispatch message based on active session state and message payload type."""
        cid = correlation_id or str(uuid.uuid4())
        logger.info("[CID:%s] Processing inbound message from %s: %s", cid, phone, message_data)

        session = self.session_manager.get_or_create_session(phone)
        msg_type = message_data.get("type", "text")

        # 1. Handle voice note greetings when IDLE
        if session.state == SessionState.IDLE and msg_type in ("audio", "voice"):
            reply = self.session_manager.handle_user_input(phone, message_text="Hi")
            await self.whatsapp_client.send_text_message(phone, reply)
            return [reply]

        # 2. In IDLE, AWAITING_LANGUAGES, or AWAITING_MENU: text state machine
        initial_states = (
            SessionState.IDLE,
            SessionState.AWAITING_LANGUAGES,
            SessionState.AWAITING_MENU,
        )
        if session.state in initial_states:
            text_body = message_data.get("text", {}).get("body", "") if msg_type == "text" else ""
            reply = self.session_manager.handle_user_input(phone, message_text=text_body)
            await self.whatsapp_client.send_text_message(phone, reply)
            return [reply]

        # 3. In Translate mode: AWAITING_TRANSLATE_INPUT
        if session.state == SessionState.AWAITING_TRANSLATE_INPUT:
            return await self._handle_translate_input(phone, message_data, cid)

        # 4. In Voice Message mode: AWAITING_VOICE_MESSAGE
        if session.state == SessionState.AWAITING_VOICE_MESSAGE:
            return await self._handle_voice_message_input(phone, message_data, cid)

        # 5. In Weather mode: AWAITING_WEATHER_LOCATION
        if session.state == SessionState.AWAITING_WEATHER_LOCATION:
            return await self._handle_weather_input(phone, message_data, cid)

        # Fallback
        reply = "Please send your input or type 'reset' to restart."
        await self.whatsapp_client.send_text_message(phone, reply)
        return [reply]

    async def _handle_translate_input(
        self, phone: str, message_data: dict[str, Any], cid: str
    ) -> list[str]:
        msg_type = message_data.get("type", "text")

        if msg_type == "text":
            text = message_data.get("text", {}).get("body", "")
            replies = await self.session_manager.process_translate_input(
                phone, input_type="text", content=text
            )
        elif msg_type in ("audio", "voice"):
            media_id = message_data.get(msg_type, {}).get("id", "")
            raw_audio = await self.whatsapp_client.download_media(media_id)
            pcm_wav = await self.audio_transcoder.ogg_to_pcm_wav(raw_audio)
            replies = await self.session_manager.process_translate_input(
                phone, input_type="audio", audio_bytes=pcm_wav
            )
        elif msg_type == "document":
            caption_or_text = message_data.get("document", {}).get("caption", "Document received")
            replies = await self.session_manager.process_translate_input(
                phone, input_type="document", content=caption_or_text
            )
        else:
            replies = await self.session_manager.process_translate_input(phone, input_type=msg_type)

        for rep in replies:
            await self.whatsapp_client.send_text_message(phone, rep)
        return replies

    async def _handle_voice_message_input(
        self, phone: str, message_data: dict[str, Any], cid: str
    ) -> list[str]:
        msg_type = message_data.get("type", "")
        if msg_type not in ("audio", "voice"):
            rep = "Please send an audio voice note in this mode, or type 'reset' to return to menu."
            await self.whatsapp_client.send_text_message(phone, rep)
            return [rep]

        media_id = message_data.get(msg_type, {}).get("id", "")
        raw_audio = await self.whatsapp_client.download_media(media_id)
        try:
            pcm_wav = await self.audio_transcoder.ogg_to_pcm_wav(raw_audio)
        except Exception:
            pcm_wav = b""

        results = await self.session_manager.process_voice_interaction(phone, pcm_wav)
        out_messages: list[str] = []

        for item in results:
            text_rep = item.get("text", "")
            if text_rep:
                await self.whatsapp_client.send_text_message(phone, text_rep)
                out_messages.append(text_rep)

            raw_tts_wav = item.get("audio_bytes")
            if raw_tts_wav:
                ogg_bytes = await self.audio_transcoder.wav_to_ogg_opus(raw_tts_wav)
                await self.whatsapp_client.send_audio_message(phone, ogg_bytes)

        return out_messages

    async def _handle_weather_input(
        self, phone: str, message_data: dict[str, Any], cid: str
    ) -> list[str]:
        msg_type = message_data.get("type", "")

        if msg_type == "location":
            loc = message_data.get("location", {})
            lat = loc.get("latitude")
            lon = loc.get("longitude")
            replies = await self.session_manager.process_weather_location(
                phone, latitude=lat, longitude=lon
            )
        elif msg_type == "text":
            city_name = message_data.get("text", {}).get("body", "")
            replies = await self.session_manager.process_weather_location(
                phone, location_text=city_name
            )
        else:
            replies = ["Please share your GPS location pin or send a city name as text."]

        for rep in replies:
            await self.whatsapp_client.send_text_message(phone, rep)
        return replies
