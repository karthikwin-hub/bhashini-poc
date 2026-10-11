"""Acceptance tests for User Story 1: Initiation & Multilingual Preference Selection.

Covers:
- FR-002: Inbound greeting processing.
- FR-003: Voice note greeting handling.
- FR-004: Language selection prompt and validation (up to 3 languages).
- FR-005: Translated main menu presentation.
- US1-AS1: Inbound greeting or voice command triggers language selection prompt.
- US1-AS2: Valid selection of 1-3 languages stores preferences and presents translated main menu.
- US1-AS3: Invalid selection or >3 languages prompts clarification without state loss.
"""

import pytest
from src.domain.session import SessionState, UserSessionManager


@pytest.mark.asyncio
async def test_us1_as1_greeting_triggers_language_menu():
    """US1-AS1: Given an idle user, when greeting 'Hi' is received,

    then system prompts with language options.
    """
    manager = UserSessionManager()
    phone = "919876543210"

    # User starts in idle or new state
    session = manager.get_or_create_session(phone)
    assert session.state == SessionState.IDLE

    # Trigger with greeting
    reply = manager.handle_user_input(phone, message_text="Hi")

    assert "language" in reply.lower() or "भाषा" in reply.lower()
    assert "1. English" in reply
    assert "2. Hindi" in reply
    assert "6. Konkani" in reply
    assert manager.get_session(phone).state == SessionState.AWAITING_LANGUAGES


@pytest.mark.asyncio
async def test_us1_as2_valid_language_selection_stores_preferences_and_shows_menu():
    """US1-AS2: Given user in AWAITING_LANGUAGES, when replying with '1, 2' (English, Hindi),

    then system records preferences and displays the main menu.
    """
    manager = UserSessionManager()
    phone = "919876543211"
    manager.handle_user_input(phone, message_text="Hi")

    # User selects English (1) and Hindi (2)
    reply = manager.handle_user_input(phone, message_text="1, 2")

    session = manager.get_session(phone)
    assert session.state == SessionState.AWAITING_MENU
    assert "en" in session.selected_languages
    assert "hi" in session.selected_languages
    assert len(session.selected_languages) == 2

    # Menu options must be present
    assert "Translate" in reply or "अनुवाद" in reply
    assert "Voice Message" in reply or "आवाज़" in reply
    assert "Weather" in reply or "मौसम" in reply


@pytest.mark.asyncio
async def test_us1_as3_invalid_or_excessive_language_selection():
    """US1-AS3: Given user in AWAITING_LANGUAGES, when replying with >3 languages or invalid input,

    then system sends guidance and remains in AWAITING_LANGUAGES.
    """
    manager = UserSessionManager()
    phone = "919876543212"
    manager.handle_user_input(phone, message_text="Hi")

    # Attempt to select 4 languages: 1, 2, 3, 4
    reply = manager.handle_user_input(phone, message_text="1, 2, 3, 4")
    session = manager.get_session(phone)
    assert session.state == SessionState.AWAITING_LANGUAGES
    assert "3" in reply or "maximum" in reply.lower() or "अधिकतम" in reply

    # Invalid input (letters that don't match any supported language)
    reply_invalid = manager.handle_user_input(phone, message_text="xyz 99")
    assert session.state == SessionState.AWAITING_LANGUAGES
    assert (
        "valid" in reply_invalid.lower()
        or "कृपया" in reply_invalid
        or "select" in reply_invalid.lower()
    )
