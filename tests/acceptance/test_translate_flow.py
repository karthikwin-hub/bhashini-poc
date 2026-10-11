"""Acceptance tests for User Story 2: Multilingual Translation (Translate).

Covers:
- FR-006: Multilingual translation for text, voice clips, and documents.
- FR-012: Graceful error handling for unsupported formats and corrupted inputs.
- US2-AS1: Text message translation into chosen languages.
- US2-AS2: Audio clip transcription via ASR and translation into chosen languages.
- US2-AS3: Document text extraction and translation into chosen languages.
- US2-AS4: Unsupported/invalid input handling in translate mode.
"""

from unittest.mock import AsyncMock

import pytest
from src.adapters.bhashini.client import BhashiniPipelineClient
from src.domain.session import SessionState, UserSessionManager


@pytest.mark.asyncio
async def test_us2_as1_text_translation_into_multiple_languages():
    """US2-AS1: Given a user in Translate mode with target languages [Hindi, Telugu],

    when text message is sent, then system returns translations in both languages.
    """
    mock_bhashini = AsyncMock(spec=BhashiniPipelineClient)
    mock_bhashini.translate_text.side_effect = lambda text, src, target: (
        f"[Hindi translation of {text}]" if target == "hi" else f"[Telugu translation of {text}]"
    )

    manager = UserSessionManager(bhashini_client=mock_bhashini)
    phone = "919876543220"

    # Setup session directly in AWAITING_TRANSLATE_INPUT with Hindi and Telugu
    session = manager.get_or_create_session(phone)
    session.state = SessionState.AWAITING_TRANSLATE_INPUT
    session.selected_languages = ["hi", "te"]

    responses = await manager.process_translate_input(
        phone=phone,
        input_type="text",
        content="What is the Mandi rate today?",
    )

    assert len(responses) == 2
    assert any("[Hindi translation" in r for r in responses)
    assert any("[Telugu translation" in r for r in responses)


@pytest.mark.asyncio
async def test_us2_as2_voice_clip_translation():
    """US2-AS2: Given user in Translate mode, when voice clip is sent,

    then audio is transcribed and translated into selected languages.
    """
    mock_bhashini = AsyncMock(spec=BhashiniPipelineClient)
    mock_bhashini.transcribe_audio.return_value = "What is the wheat price?"
    mock_bhashini.translate_text.side_effect = lambda text, src, target: (
        f"[Hindi of {text}]" if target == "hi" else f"[Tamil of {text}]"
    )

    manager = UserSessionManager(bhashini_client=mock_bhashini)
    phone = "919876543221"
    session = manager.get_or_create_session(phone)
    session.state = SessionState.AWAITING_TRANSLATE_INPUT
    session.selected_languages = ["hi", "ta"]

    responses = await manager.process_translate_input(
        phone=phone,
        input_type="audio",
        audio_bytes=b"dummy_wav_pcm_bytes",
    )

    assert len(responses) == 2
    assert any("[Hindi of" in r for r in responses)
    assert any("[Tamil of" in r for r in responses)


@pytest.mark.asyncio
async def test_us2_as3_document_translation():
    """US2-AS3: Given user in Translate mode with languages [English, Konkani],

    when text document is sent, then extracted text is translated.
    """
    mock_bhashini = AsyncMock(spec=BhashiniPipelineClient)
    mock_bhashini.translate_text.side_effect = lambda text, src, target: (
        f"[English: {text}]" if target == "en" else f"[Konkani: {text}]"
    )

    manager = UserSessionManager(bhashini_client=mock_bhashini)
    phone = "919876543222"
    session = manager.get_or_create_session(phone)
    session.state = SessionState.AWAITING_TRANSLATE_INPUT
    session.selected_languages = ["en", "gom"]

    doc_content = "Annual harvest report 2026."
    responses = await manager.process_translate_input(
        phone=phone,
        input_type="document",
        content=doc_content,
    )

    assert len(responses) == 2
    assert any("[English:" in r for r in responses)
    assert any("[Konkani:" in r for r in responses)


@pytest.mark.asyncio
async def test_us2_as4_unsupported_media_input():
    """US2-AS4: Given user in Translate mode, when unsupported media is sent,

    then system sends an error message without crashing.
    """
    manager = UserSessionManager()
    phone = "919876543223"
    session = manager.get_or_create_session(phone)
    session.state = SessionState.AWAITING_TRANSLATE_INPUT
    session.selected_languages = ["hi"]

    responses = await manager.process_translate_input(
        phone=phone,
        input_type="video",
        content=None,
    )

    assert len(responses) == 1
    assert (
        "unsupported" in responses[0].lower()
        or "कृपया" in responses[0]
        or "text" in responses[0].lower()
    )
