"""Acceptance tests for User Story 3: Vernacular Voice-in, Voice-out Interaction.

Covers:
- FR-007: Voice note input transcription, translation, and speech synthesis.
- US3-AS1: Voice note transcribed, translated, synthesized into speech (ASR + NMT + TTS).
- US3-AS2: Synthesized audio returned as audio note payload for WhatsApp.
- US3-AS3: Silent or corrupted audio triggers graceful recovery.
"""

from unittest.mock import AsyncMock

import pytest
from src.adapters.bhashini.client import BhashiniPipelineClient
from src.domain.session import SessionState, UserSessionManager


@pytest.mark.asyncio
async def test_us3_as1_and_as2_voice_in_voice_and_text_out():
    """US3-AS1 & US3-AS2: Given user in Voice Message mode with target languages [Hindi, Telugu],

    when incoming audio voice note is received, then system transcribes, translates, synthesizes,
    and returns both text and audio messages.
    """
    mock_bhashini = AsyncMock(spec=BhashiniPipelineClient)
    mock_bhashini.transcribe_audio.return_value = "नमस्ते, आज का मौसम कैसा है?"
    mock_bhashini.translate_and_tts.side_effect = lambda text, src, target: (
        (f"Translation to {target}: {text}", b"RIFF_FAKE_WAV_BYTES_DATA")
    )

    manager = UserSessionManager(bhashini_client=mock_bhashini)
    phone = "919876543230"
    session = manager.get_or_create_session(phone)
    session.state = SessionState.AWAITING_VOICE_MESSAGE
    session.selected_languages = ["hi", "te"]

    results = await manager.process_voice_interaction(
        phone=phone,
        audio_bytes=b"raw_user_voice_bytes",
    )

    assert len(results) == 2  # Two languages
    for item in results:
        assert "text" in item
        assert "audio_bytes" in item
        assert len(item["audio_bytes"]) > 0
        assert item["audio_bytes"].startswith(b"RIFF")


@pytest.mark.asyncio
async def test_us3_as3_corrupted_or_silent_voice_message():
    """US3-AS3: Given user in Voice Message mode, when audio is empty or unparseable,

    then system sends a polite clarification text without crashing.
    """
    mock_bhashini = AsyncMock(spec=BhashiniPipelineClient)
    mock_bhashini.transcribe_audio.side_effect = ValueError("Empty or inaudible audio stream")

    manager = UserSessionManager(bhashini_client=mock_bhashini)
    phone = "919876543231"
    session = manager.get_or_create_session(phone)
    session.state = SessionState.AWAITING_VOICE_MESSAGE
    session.selected_languages = ["hi"]

    results = await manager.process_voice_interaction(
        phone=phone,
        audio_bytes=b"empty_or_bad_audio",
    )

    assert len(results) == 1
    # Should deliver fallback explanation text and no audio
    assert "audio_bytes" not in results[0] or results[0]["audio_bytes"] is None
    assert (
        "माफ़" in results[0]["text"]
        or "sorry" in results[0]["text"].lower()
        or "आवाज़" in results[0]["text"]
    )
