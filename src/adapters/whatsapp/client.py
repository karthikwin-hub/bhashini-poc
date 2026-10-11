"""WhatsApp Business Cloud API client adapter."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class WhatsAppClient:
    """Client for Meta WhatsApp Business Cloud API."""

    def __init__(
        self,
        token: str | None = None,
        phone_number_id: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.token = token or ""
        self.phone_number_id = phone_number_id or ""
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=20.0)
        return self._client

    async def send_text_message(self, to_phone: str, text: str) -> dict[str, Any]:
        """Send an outbound text message to a WhatsApp recipient."""
        if not self.token or not self.phone_number_id:
            logger.info("WhatsApp credentials not set; mock text to %s: %s", to_phone, text)
            return {"messages": [{"id": "wamid.mock_text"}]}

        client = await self._get_client()
        url = f"{GRAPH_API_BASE}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def upload_audio_media(self, audio_bytes: bytes, filename: str = "voice.ogg") -> str:
        """Upload audio bytes to WhatsApp media store and return media_id."""
        if not self.token or not self.phone_number_id:
            logger.info("WhatsApp credentials not set; returning mock media id.")
            return "mock_media_id_12345"

        client = await self._get_client()
        url = f"{GRAPH_API_BASE}/{self.phone_number_id}/media"
        headers = {"Authorization": f"Bearer {self.token}"}
        files = {
            "file": (filename, audio_bytes, "audio/ogg"),
        }
        data = {
            "messaging_product": "whatsapp",
            "type": "audio/ogg",
        }

        resp = await client.post(url, headers=headers, data=data, files=files)
        resp.raise_for_status()
        res_data = resp.json()
        return res_data.get("id", "")

    async def send_audio_message(self, to_phone: str, audio_bytes: bytes) -> dict[str, Any]:
        """Upload and dispatch an audio voice message to recipient."""
        media_id = await self.upload_audio_media(audio_bytes)
        if not self.token or not self.phone_number_id:
            return {"messages": [{"id": f"wamid.mock_audio_{media_id}"}]}

        client = await self._get_client()
        url = f"{GRAPH_API_BASE}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "audio",
            "audio": {"id": media_id},
        }

        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def download_media(self, media_id: str) -> bytes:
        """Fetch media URL and download raw bytes from Meta CDN."""
        if not self.token:
            logger.info("Mock download for media %s", media_id)
            return b"mock_audio_media_bytes"

        client = await self._get_client()
        info_url = f"{GRAPH_API_BASE}/{media_id}"
        headers = {"Authorization": f"Bearer {self.token}"}

        resp = await client.get(info_url, headers=headers)
        resp.raise_for_status()
        media_url = resp.json().get("url", "")
        if not media_url:
            raise ValueError(f"No download URL returned for media {media_id}")

        file_resp = await client.get(media_url, headers=headers)
        file_resp.raise_for_status()
        return file_resp.content
