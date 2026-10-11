# Tasks: WhatsApp Multilingual Bot

**Feature**: `001-whatsapp-multilingual-bot`  
**Input**: Design documents from `specs/001-whatsapp-multilingual-bot/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`  

---

## Phase 1: Setup & Configuration

**Purpose**: Core environment settings and configuration injection

- [x] T001 Create environment settings loader in `src/api/config.py` reading Infisical variables (`BHASHINI_USER_ID`, `BHASHINI_API_KEY`, `BHASHINI_PIPELINE_ID`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`)

---

## Phase 2: Foundational Domain & Adapters

**Purpose**: Foundational domain models and external client adapters that user stories depend on

- [x] T002 [P] Implement pure `UserSession`, `SessionState`, and `LanguageValidator` in `src/domain/session.py` (covers `FR-002`, `FR-004`)
- [x] T003 [P] Implement pure translation data models in `src/domain/translation.py`
- [x] T004 [P] Implement pure weather data models and summary generators in `src/domain/weather.py`
- [x] T005 [P] Implement in-memory audio transcoder using FFmpeg in `src/adapters/audio/transcoder.py`
- [x] T006 [P] Implement Bhashini client adapter (ASR, NMT, TTS) in `src/adapters/bhashini/client.py` (covers `FR-006`, `FR-007`)
- [x] T007 [P] Implement WhatsApp Business Cloud API client in `src/adapters/whatsapp/client.py` (covers `FR-001`, `FR-007`)
- [x] T008 [P] Implement Open-Meteo weather client in `src/adapters/weather/client.py` (covers `FR-008`)

---

## Phase 3: User Story 1 - Initiation & Language Preference Selection (Priority: P1) 🎯 MVP

**Goal**: Enable users to initiate chat with greeting/voice, select up to 3 languages, and receive the main menu translated into those languages.

### Tests for User Story 1 (Write First) ⚠️
- [x] T010 [P] [US1] Write acceptance tests for `US1-AS1`, `US1-AS2`, and `US1-AS3` in `tests/acceptance/test_language_selection.py`
- [x] T011 [P] [US1] Write unit tests for language validation and session transitions in `tests/unit/test_session_domain.py` (covers `FR-003`, `FR-004`, `FR-009`)

### Implementation for User Story 1
- [x] T012 [US1] Implement interactive language prompt generation and validation logic in `src/domain/session.py` (covers `FR-004`)
- [x] T013 [US1] Implement main menu translation and presentation logic in `src/api/worker.py` (covers `FR-005`)
- [x] T014 [US1] Integrate User Story 1 flow into interaction worker in `src/api/worker.py`

**Checkpoint**: User Story 1 fully testable independently via `tests/acceptance/test_language_selection.py`.

---

## Phase 4: User Story 2 - Multilingual Translation ("Translate") (Priority: P1)

**Goal**: Process user text, document, or audio clips and deliver translated text messages in the user's chosen languages.

### Tests for User Story 2 (Write First) ⚠️
- [x] T020 [P] [US2] Write acceptance tests for `US2-AS1`, `US2-AS2`, `US2-AS3`, `US2-AS4` in `tests/acceptance/test_translate_flow.py` (covers `FR-006`, `FR-012`)

### Implementation for User Story 2
- [x] T021 [US2] Implement text message translation handler in `src/api/worker.py` (covers `FR-006`)
- [x] T022 [US2] Implement audio clip transcription and translation handler in `src/api/worker.py` (covers `FR-006`)
- [x] T023 [US2] Implement document text extraction and translation handler in `src/api/worker.py` (covers `FR-006`)
- [x] T024 [US2] Add input validation and error fallbacks for unsupported formats in `src/api/worker.py` (covers `FR-012`)

**Checkpoint**: User Story 2 fully testable independently via `tests/acceptance/test_translate_flow.py`.

---

## Phase 5: User Story 3 - Vernacular Voice-in, Voice-out ("Voice Message") (Priority: P1)

**Goal**: Enable voice note input with speech recognition, multilingual translation, and audio voice synthesis back to WhatsApp.

### Tests for User Story 3 (Write First) ⚠️
- [x] T030 [P] [US3] Write acceptance tests for `US3-AS1`, `US3-AS2`, `US3-AS3` in `tests/acceptance/test_voice_message_flow.py` (covers `FR-007`)

### Implementation for User Story 3
- [x] T031 [US3] Implement voice note processing pipeline (FFmpeg transcode $\rightarrow$ Bhashini ASR) in `src/api/worker.py` (covers `FR-007`)
- [x] T032 [US3] Implement multilingual speech synthesis (Bhashini TTS) and WhatsApp audio upload dispatch in `src/api/worker.py` (covers `FR-007`)
- [x] T033 [US3] Add silent/corrupted audio detection and vernacular error messaging in `src/api/worker.py`

**Checkpoint**: User Story 3 fully testable independently via `tests/acceptance/test_voice_message_flow.py`.

---

## Phase 6: User Story 4 - Multilingual Weather Advisory ("Weather") (Priority: P2)

**Goal**: Provide current and next day weather forecasts based on GPS location or city name, translated into target languages.

### Tests for User Story 4 (Write First) ⚠️
- [x] T040 [P] [US4] Write acceptance tests for `US4-AS1`, `US4-AS2`, `US4-AS3` in `tests/acceptance/test_weather_flow.py` (covers `FR-008`)

### Implementation for User Story 4
- [x] T041 [US4] Implement GPS coordinates handler and Open-Meteo weather fetch in `src/api/worker.py` (covers `FR-008`)
- [x] T042 [US4] Implement city/town text geocoding and forecast fetch in `src/api/worker.py` (covers `FR-008`)
- [x] T043 [US4] Implement weather forecast translation via Bhashini NMT and dispatch in `src/api/worker.py` (covers `FR-008`)

**Checkpoint**: User Story 4 fully testable independently via `tests/acceptance/test_weather_flow.py`.

---

## Phase 7: Webhook Ingestion & API Routing

**Purpose**: Assemble HTTP routes, Meta webhook handshake, and decoupled worker dispatch

- [x] T050 Implement GET `/webhook` handshake and POST `/webhook` event ingestion in `src/api/routes/webhook.py` (covers `FR-001`, `FR-010`)
- [x] T051 Register webhook routes and lifecycle handlers in `src/api/app.py`
- [x] T052 Implement structured logging with correlation IDs in `src/api/worker.py` (covers `FR-010`)

---

## Phase 8: Verification & Quality Gate G3

**Purpose**: Verify all tests and sensor checks pass before build conclusion

- [x] T060 Run full sensor verification (`python scripts/harness/verify.py`)
- [x] T061 Validate 100% strict requirement traceability (`python scripts/harness/check_traceability.py --strict`)
- [x] T062 Update `progress.md` and `checks.md` with execution evidence
