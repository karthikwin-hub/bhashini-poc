"""Unit tests for session domain models, language validation, and transitions.

Covers:
- FR-003: Voice note and greeting handling.
- FR-004: Language selection prompt and validation.
- FR-009: Session reset and timeout handling.
"""

from src.domain.session import (
    LanguageValidator,
    SessionState,
    UserSessionManager,
)


def test_language_validator_single_and_multiple():
    """Test parsing 1 to 3 valid language tokens."""
    codes, err = LanguageValidator.parse_selection("1")
    assert err is None
    assert codes == ["en"]

    codes, err = LanguageValidator.parse_selection("1, 2, 3")
    assert err is None
    assert codes == ["en", "hi", "te"]

    # Names and aliases
    codes, err = LanguageValidator.parse_selection("Hindi, telugu, Konkani")
    assert err is None
    assert codes == ["hi", "te", "gom"]


def test_language_validator_rejects_exceeding_limit():
    """Test rejection when user attempts to select more than 3 languages."""
    codes, err = LanguageValidator.parse_selection("1, 2, 3, 4")
    assert codes == []
    assert err is not None
    assert "maximum of 3" in err


def test_language_validator_rejects_empty_or_invalid():
    """Test rejection of blank input or invalid garbage tokens."""
    codes, err = LanguageValidator.parse_selection("")
    assert codes == []
    assert err is not None

    codes, err = LanguageValidator.parse_selection("foo bar baz")
    assert codes == []
    assert err is not None
    assert "valid" in err.lower()


def test_session_state_transitions():
    """Test state machine progression from IDLE through Menu selection."""
    manager = UserSessionManager()
    phone = "919000000001"

    # Start
    session = manager.get_or_create_session(phone)
    assert session.state == SessionState.IDLE

    # Greeting -> AWAITING_LANGUAGES
    prompt = manager.handle_user_input(phone, "Hello")
    assert "Please select" in prompt
    assert session.state == SessionState.AWAITING_LANGUAGES

    # Select languages -> AWAITING_MENU
    menu = manager.handle_user_input(phone, "1, 2")
    assert "Main Menu" in menu
    assert session.state == SessionState.AWAITING_MENU
    assert session.selected_languages == ["en", "hi"]

    # Select Translate mode -> AWAITING_TRANSLATE_INPUT
    t_prompt = manager.handle_user_input(phone, "1")
    assert "Translate mode" in t_prompt
    assert session.state == SessionState.AWAITING_TRANSLATE_INPUT

    # Reset (FR-009)
    r_prompt = manager.handle_user_input(phone, "reset")
    assert session.state == SessionState.AWAITING_LANGUAGES
    assert "Please select" in r_prompt
