# Feature Specification: WhatsApp Multilingual Bot with Bhashini Integration

**Feature Branch**: `001-whatsapp-multilingual-bot`  
**Created**: 2026-10-11  
**Status**: Draft (Ready for Gate G1 "Spec Ready" Review)  
**Input**: User prompt: WhatsApp accessibility, language selection (up to 3 from English, Hindi, Telugu, Bengali, Tamil, Konkani), 3 core capabilities: Translate, Voice Message, Weather.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initiation & Multilingual Preference Selection (Priority: P1)
As a WhatsApp user (using a personal or business number),  
I want to initiate a chat with "Hi" or a voice command ("show menu") and select up to three preferred languages from English, Hindi, Telugu, Bengali, Tamil, and Konkani,  
So that all subsequent interactions, menus, and responses are delivered in my chosen languages.

**Why this priority**: Without initiating the conversation and establishing language preferences, no downstream features (Translate, Voice Message, Weather) can function.

**Independent Test**: Can be verified by sending "Hi" or sending an audio note saying "show menu", verifying the interactive language prompt, selecting 1–3 languages (e.g., "1, 2" for English and Hindi), and confirming the main menu is presented in those languages.

**Acceptance Scenarios**:
1. **US1-AS1**: **Given** a new user or user in idle state, **When** they send a text greeting ("Hi", "Hello") or send an audio note stating "show menu", **Then** the bot replies acknowledging the greeting and invites them to select up to 3 languages from the supported list: 1. English, 2. Hindi, 3. Telugu, 4. Bengali, 5. Tamil, 6. Konkani.
2. **US1-AS2**: **Given** a user prompted for language selection, **When** they reply with valid selections (e.g., "1, 2" or "Hindi, Telugu"), **Then** the system records up to 3 chosen target languages in the user session and presents the main menu (1. Translate, 2. Voice Message, 3. Weather) translated into the selected languages.
3. **US1-AS3** *(Negative Case)*: **Given** a user prompted for language selection, **When** they select more than 3 languages or provide invalid numbers/text, **Then** the system sends a friendly clarification message asking them to choose between 1 and 3 valid languages from the list without losing session state.

---

### User Story 2 - Multilingual Text, Document, and Audio Translation ("Translate") (Priority: P1)
As a user who has chosen their target languages and selected "Translate",  
I want to submit text, upload a document, or send a voice clip,  
So that the system translates the content into each of my selected languages and sends the translations back as WhatsApp text messages.

**Why this priority**: Core translation utility enabling citizens and business users to convert text or speech across Indic languages rapidly.

**Independent Test**: Send text "What is the crop price today?" after selecting Hindi and Telugu; verify bot responds with accurate translated text messages in both Hindi and Telugu.

**Acceptance Scenarios**:
1. **US2-AS1**: **Given** a user in the Translate mode with target languages [Hindi, Telugu], **When** they send a text message, **Then** the system invokes Bhashini NMT and returns translated text messages for Hindi and Telugu.
2. **US2-AS2**: **Given** a user in the Translate mode with target languages [Hindi, Tamil], **When** they send an audio/voice clip, **Then** the system transcodes the audio to 16kHz PCM WAV, transcribes it via Bhashini ASR, translates the transcript into Hindi and Tamil, and delivers the translated texts back to the user.
3. **US2-AS3**: **Given** a user in the Translate mode with target languages [English, Konkani], **When** they upload a text/document file (`.txt`), **Then** the system extracts the text, translates it into English and Konkani via Bhashini NMT, and sends back the translated texts.
4. **US2-AS4** *(Negative Case)*: **Given** a user in Translate mode, **When** an empty message or unsupported binary media (e.g. video file) is sent, **Then** the system alerts the user and prompts them to provide text, a voice clip, or a text document.

---

### User Story 3 - Vernacular Voice-in, Voice-out Interaction ("Voice Message") (Priority: P1)
As a vernacular-speaking user who selected "Voice Message",  
I want to speak directly into WhatsApp in my regional dialect,  
So that the system transcribes my speech, translates it into my selected languages, and replies with BOTH text messages and synthesized audio voice notes in each language.

**Why this priority**: Essential for rural accessibility and low-literacy users who rely on voice communication rather than reading text.

**Independent Test**: Send an audio note in Hindi; verify bot sends back a text translation AND an audio voice message playable in WhatsApp in the requested languages.

**Acceptance Scenarios**:
1. **US3-AS1**: **Given** a user in Voice Message mode with target languages [Hindi, Telugu], **When** they send an incoming WhatsApp voice note, **Then** the system downloads the audio, transcodes it, runs Bhashini ASR, translates the recognized text into Hindi and Telugu, synthesizes audio via Bhashini TTS for both languages, and sends back the text and synthesized audio notes.
2. **US3-AS2**: **Given** a user in Voice Message mode, **When** synthesized audio is generated by Bhashini TTS, **Then** the system uploads the audio to WhatsApp Cloud Media API (`audio/wav`) and sends it as an audio message playable inside WhatsApp.
3. **US3-AS3** *(Negative Case)*: **Given** a user in Voice Message mode, **When** the incoming voice audio is corrupted, silent, or unparseable by ASR, **Then** the system sends a courteous vernacular error text asking the user to re-record in a quiet environment.

---

### User Story 4 - Multilingual Weather Advisory ("Weather") (Priority: P2)
As a user who selected "Weather",  
I want to share my WhatsApp GPS location or type my city/village name,  
So that the system fetches the current and next day's weather forecast and delivers it in my selected languages.

**Why this priority**: High-value daily utility for farmers, traders, and citizens requiring vernacular weather advisories.

**Independent Test**: Send a WhatsApp location pin or text "Panaji"; verify current day and next day weather update is returned translated into the user's selected languages.

**Acceptance Scenarios**:
1. **US4-AS1**: **Given** a user in Weather mode, **When** they share a WhatsApp location message (latitude and longitude), **Then** the system queries the weather service (Open-Meteo) for current and next day forecast, translates the forecast into the user's selected languages via Bhashini NMT, and sends the text report back.
2. **US4-AS2**: **Given** a user in Weather mode without location sharing enabled, **When** they provide a city/village name text (e.g., "Hyderabad" or "Varanasi"), **Then** the system geocodes the location, retrieves the 2-day forecast, translates it, and sends the multilingual forecast text.
3. **US4-AS3** *(Negative Case)*: **Given** a user in Weather mode, **When** an unrecognizable location string is sent, **Then** the system prompts them to specify a nearby major town or share their WhatsApp location pin.

---

### Edge Cases
- **Language Switching**: User typing "reset", "menu", or "show menu" at any time resets the state to language selection or main menu.
- **Session Expiry**: User conversation states are maintained in a clean session store with graceful timeout recovery (idle > 2 hours re-greets user).
- **Network Timeouts on Bhashini / Meta**: Webhook endpoints must immediately return HTTP 200 OK within 5 seconds to Meta, offloading ASR/NMT/TTS pipeline processing to background workers.
- **Multiple Media Uploads**: If a user sends multiple attachments concurrently, each is queued and processed sequentially with progress indicators.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept inbound WhatsApp Cloud API webhook notifications (`/webhook` GET verification and POST event handling).
- **FR-002**: System MUST identify incoming sender phone numbers and maintain conversation state (idle, language selection, menu selection, translate, voice message, weather).
- **FR-003**: System MUST support initiating conversation via text greetings ("Hi", "Hello", "menu") or voice note command ("show menu").
- **FR-004**: System MUST prompt and store up to 3 selected languages from: English (`en`), Hindi (`hi`), Telugu (`te`), Bengali (`bn`), Tamil (`ta`), and Konkani (`gom`/`kok`).
- **FR-005**: System MUST present a 3-option main menu ("1. Translate", "2. Voice Message", "3. Weather") translated into the user's selected languages.
- **FR-006**: In Translate mode, system MUST accept text, plain text documents, or audio clips, translate the content into all selected languages via Bhashini NMT, and reply via WhatsApp text.
- **FR-007**: In Voice Message mode, system MUST accept WhatsApp audio messages, transcode OGG Opus to 16kHz PCM WAV, run Bhashini ASR, translate via Bhashini NMT, synthesize voice via Bhashini TTS, and dispatch both text and audio messages back to the user.
- **FR-008**: In Weather mode, system MUST accept WhatsApp GPS location coordinates or city/town text names, query a weather forecast API for current and next day metrics (temperature, conditions, rain), translate the summary via Bhashini NMT, and reply with multilingual text messages.
- **FR-009**: System MUST allow users to reset their session or re-open the language menu by sending "menu", "reset", or "show menu".
- **FR-010**: System MUST decouple incoming webhook acknowledgment (returning HTTP 200 within 5 seconds) from long-running Bhashini ASR/TTS/NMT compute pipelines using background task execution.
- **FR-011**: System MUST retrieve all credentials (`BHASHINI_USER_ID`, `BHASHINI_API_KEY`, `BHASHINI_PIPELINE_ID`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`) from Infisical environment variables at runtime.
- **FR-012**: System MUST handle pipeline errors and service downtimes gracefully by delivering a fallback vernacular error message without crashing.

---

### Key Entities

- **UserSession**:
  - `phone_number`: String (E.164 phone number)
  - `state`: Enum (`IDLE`, `AWAITING_LANGUAGES`, `AWAITING_MENU`, `AWAITING_TRANSLATE_INPUT`, `AWAITING_VOICE_MESSAGE`, `AWAITING_WEATHER_LOCATION`)
  - `selected_languages`: List[str] (max 3 language codes)
  - `last_active_at`: Timestamp
- **ConversationMessage**:
  - `message_id`: String (Meta message ID)
  - `sender_id`: String
  - `message_type`: Enum (`text`, `audio`, `document`, `location`)
  - `payload`: Text or media reference
- **TranslationResult**:
  - `source_text`: String
  - `source_language`: String
  - `translations`: Dict[str, str] (language_code -> translated_text)
- **VoiceSynthesisResult**:
  - `language_code`: String
  - `audio_bytes`: Binary audio stream (WAV)
- **WeatherForecast**:
  - `location_name`: String
  - `current_day_summary`: String
  - `next_day_summary`: String

---

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: 100% of incoming valid WhatsApp webhook events are acknowledged with HTTP 200 OK within 3 seconds.
- **SC-002**: Users can complete language selection (1–3 languages) in 2 simple WhatsApp turns.
- **SC-003**: In "Voice Message" mode, end-to-end processing (ASR transcription + NMT translation + TTS synthesis) completes and dispatches both text and voice responses within 25 seconds for audio clips under 30 seconds.
- **SC-004**: In "Weather" mode, weather forecast for current day and next day is retrieved and translated into all selected languages within 8 seconds.

---

## Assumptions
- During testing, the user's personal WhatsApp number will be registered as a test recipient in the Meta Developer App console until a dedicated WhatsApp Business account is provisioned.
- Bhashini pipeline endpoints for ASR, NMT, and TTS support the requested Indic languages (`en`, `hi`, `te`, `bn`, `ta`, `gom`/`kok`).
- Weather metrics will be retrieved via Open-Meteo (open-source, no key required, high availability) or equivalent weather provider.
- Audio transcoding uses local FFmpeg binary for converting incoming OGG Opus to 16kHz PCM WAV.

---

## Scope Boundaries *(mandatory — Agentic Delivery Standard)*
- **In scope**:
  - WhatsApp webhook endpoint (verification & event ingestion).
  - Multi-turn state machine (greeting, language selection, menu routing).
  - Bhashini client adapter (ASR, NMT, TTS) for `en`, `hi`, `te`, `bn`, `ta`, `gom`/`kok`.
  - Translate module (text, audio clip, text document).
  - Voice Message module (speech in, translated speech + text out).
  - Weather module (GPS pin or text city -> current + next day forecast -> translated text out).
  - Infisical environment integration.
- **Out of scope**:
  - Paid/proprietary weather API subscriptions.
  - Video or complex image OCR processing (focused on text, voice, and text docs).
  - Direct financial transaction processing.
- **Must not change**:
  - Existing `/health` endpoint response schema (`{"status": "ok", "service": "bhashini-app"}`).
  - Verification harness scripts (`scripts/harness/*`).
  - Strict zero-leak Infisical secrets policy.

---

## Non-Functional Requirements *(mandatory — measurable)*
- **NFR-001** Performance: Webhook acknowledgment HTTP 200 response time < 3.0s; total async pipeline execution < 25s for 3-language voice translation.
- **NFR-002** Security & Privacy: No citizen audio recordings or message bodies logged to persistent disk; zero secrets written to `.env` files; all credentials injected via Infisical.
- **NFR-003** Reliability: Idempotent message handling based on WhatsApp `message_id` to prevent duplicate processing on webhook retries.
- **NFR-004** Observability: Structured logging with correlation ID per WhatsApp message event; pipeline latency metrics logged for ASR, NMT, and TTS stages.
- **NFR-005** Usability: Conversational messages formatted with clean WhatsApp Markdown (bolding, numbered menus, emojis).
- **NFR-006** Audio Compatibility: 16kHz mono 16-bit PCM WAV for Bhashini ASR and WhatsApp audio message upload.

---

## Data and Integration Contracts
- **Meta WhatsApp Cloud API (v21.0)**:
  - Inbound webhook: POST `/webhook` with JSON payload containing `entry[].changes[].value.messages[]`.
  - Media download: GET `https://graph.facebook.com/v21.0/{media_id}` -> temporary CDN URL -> binary download.
  - Text dispatch: POST `https://graph.facebook.com/v21.0/{phone_number_id}/messages` with `{"type": "text", "text": {"body": "..."}}`.
  - Audio dispatch: POST `https://graph.facebook.com/v21.0/{phone_number_id}/media` (`audio/wav`) -> POST message with `{"type": "audio", "audio": {"id": "..."}}`.
- **Bhashini ULCA / Dhruva API**:
  - Config: POST `https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline`
  - Compute: POST callback URL with inference headers and payload for `asr`, `translation`, `tts`.
- **Weather API (Open-Meteo)**:
  - Forecast: GET `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto`
  - Geocoding: GET `https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en`

---

## Testing Requirements *(mandatory)*
- Automated unit tests for:
  - Language selection validator and session state transitions.
  - Webhook verification and event deserialization.
  - Weather parsing and forecast formatting.
  - Audio transcoding helper.
- Automated acceptance tests covering:
  - `US1-AS1` through `US1-AS3`: Initiation & Language Selection.
  - `US2-AS1` through `US2-AS4`: Translate flow (text, audio, document).
  - `US3-AS1` through `US3-AS3`: Voice Message flow (ASR + NMT + TTS).
  - `US4-AS1` through `US4-AS3`: Weather flow (GPS and text location).
- Requirement-to-test traceability verified via `python scripts/harness/check_traceability.py`.

---

## Spec Quality Checklist — Gate G1 "Spec Ready"
- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Each FR states one testable behaviour with an ID (`FR-001` through `FR-012`)
- [x] Each user story has numbered Given/When/Then scenarios including negative cases (`US1-AS1`..`US4-AS3`)
- [x] Every FR is exercised by at least one scenario
- [x] NFRs are measurable; success criteria are measurable
- [x] In scope / out of scope / must-not-change are explicit
- [ ] Spec owner approval: Pending human review
