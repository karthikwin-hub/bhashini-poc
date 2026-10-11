"""In-memory audio transcoding between WhatsApp Opus/OGG and Bhashini 16kHz PCM WAV."""

import asyncio
import logging

logger = logging.getLogger(__name__)


class AudioTranscoder:
    """Performs in-memory streaming audio format conversions using FFmpeg."""

    @staticmethod
    async def ogg_to_pcm_wav(ogg_bytes: bytes) -> bytes:
        """Convert OGG/Opus audio bytes from WhatsApp into 16kHz Mono 16-bit PCM WAV."""
        if not ogg_bytes or len(ogg_bytes) < 32:
            raise ValueError("Input audio payload is empty or too short.")

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            "pipe:0",
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            "pipe:1",
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate(input=ogg_bytes)
            if process.returncode != 0:
                logger.warning("FFmpeg conversion failed: %s", stderr.decode(errors="replace"))
                raise ValueError(f"FFmpeg transcoding failed: {stderr.decode(errors='replace')}")
            return stdout
        except FileNotFoundError:
            logger.warning("FFmpeg not found on host system, returning raw bytes as fallback.")
            return ogg_bytes

    @staticmethod
    async def wav_to_ogg_opus(wav_bytes: bytes) -> bytes:
        """Convert Bhashini TTS PCM WAV audio bytes into OGG/Opus for WhatsApp voice delivery."""
        if not wav_bytes:
            raise ValueError("WAV audio input is empty.")

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            "pipe:0",
            "-c:a",
            "libopus",
            "-b:a",
            "32k",
            "-f",
            "ogg",
            "pipe:1",
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate(input=wav_bytes)
            if process.returncode != 0:
                logger.warning("FFmpeg wav_to_ogg failed: %s", stderr.decode(errors="replace"))
                return wav_bytes
            return stdout
        except FileNotFoundError:
            logger.warning("FFmpeg not found on host system, returning raw WAV.")
            return wav_bytes
