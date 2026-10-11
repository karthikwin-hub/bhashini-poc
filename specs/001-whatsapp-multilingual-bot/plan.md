# Implementation Plan: WhatsApp Multilingual Bot

**Branch**: `001-whatsapp-multilingual-bot` | **Date**: 2026-10-11 | **Spec**: [`specs/001-whatsapp-multilingual-bot/spec.md`](file:///home/puja/Documents/Cursor/bhashini-poc/specs/001-whatsapp-multilingual-bot/spec.md)

---

## 1. Summary

Implement an enterprise-grade WhatsApp conversational bot service integrating India's sovereign AI infrastructure (Project Bhashini ULCA/Dhruva APIs) for speech recognition (ASR), neural machine translation (NMT), and text-to-speech voice synthesis (TTS), coupled with Open-Meteo weather intelligence. 

The application architecture enforces strict clean boundaries:
- **Presentation / API (`src/api/`)**: Validates Meta webhook handshakes, ingest incoming events, schedules background workers.
- **Domain (`src/domain/`)**: Pure state machine for user session lifecycle (greeting, language selection up to 3 Indic languages, menu dispatch), language validation, weather models, translation models.
- **Adapters (`src/adapters/`)**: Isolated external network calls to Bhashini API, WhatsApp Cloud API, Open-Meteo weather service, and in-memory FFmpeg audio transcoder.
- **Security**: Injected at runtime via Infisical (`bhashini-poc` project).

---

## 2. Technical Context

- **Language/Version**: Python 3.12+
- **Primary Dependencies**: FastAPI (0.143+), Uvicorn (0.54+), HTTPX (0.28+ async), Pydantic (2.14+), python-dotenv (1.2+)
- **Dev & Test Tooling**: `uv` package manager, Ruff (0.17+ format & lint), Pytest (9.1+), Pytest-Asyncio (1.4+)
- **System Tooling**: FFmpeg (for memory-piped OGG Opus $\leftrightarrow$ 16kHz PCM WAV transcoding)
- **External Services**:
  - Bhashini ULCA/Dhruva inference endpoints (`meity-auth.ulcacontrib.org`)
  - Meta WhatsApp Business Cloud API (`graph.facebook.com/v21.0`)
  - Open-Meteo Weather Forecast & Geocoding APIs
- **Secrets Management**: Infisical CLI (`project: bhashini-poc`)

---

## 3. Constitution Check (Gate G2 Prerequisites)

| Principle | Assessment | Status |
|---|---|---|
| **I. Spec Before Implementation** | Spec approved with testable scenarios and FR IDs (`US1-AS1`..`US4-AS3`, `FR-001`..`FR-012`). | **PASS** |
| **II. Testable Requirements & Traceability** | Acceptance tests mapped for each scenario before building production code. | **PASS** |
| **III. Verification Before Done** | Sensor suite runs in one command (`python scripts/harness/verify.py`). | **PASS** |
| **IV. Smallest Sufficient Change** | Reuses existing stdlib, httpx, and fastapi without adding unneeded third-party frameworks. | **PASS** |
| **V. Architecture Boundaries** | Pure `src/domain/` has 0 framework imports; `src/adapters/` encapsulates all I/O; `src/api/` routes only. | **PASS** |
| **VI. Security & Privacy** | Infisical runtime injection; zero disk logging of citizen messages or voice notes. | **PASS** |
| **VII. Observability** | Correlation ID tracking per WhatsApp interaction; structured logging. | **PASS** |
| **VIII. Small, Reversible Delivery** | Feature isolated on `001-whatsapp-multilingual-bot` branch; 1-command git rollback. | **PASS** |
| **IX. Human Accountability** | Gate G1 & G2 checkpoints enforced; human tech lead review. | **PASS** |
| **X. Continuous Harness Improvement** | SDD harness doctor and sensor checks clean. | **PASS** |

---

## 4. Project Structure

### Documentation & Spec Assets
```text
specs/001-whatsapp-multilingual-bot/
├── spec.md                  # Approved feature requirements and scenarios
├── plan.md                  # This implementation architecture plan
├── research.md              # Research on Bhashini, WhatsApp, and Weather APIs
├── data-model.md            # Session state machine and data entities
├── quickstart.md            # Local execution and verification runbook
├── contracts/
│   ├── whatsapp.json        # WhatsApp webhook and message schemas
│   └── bhashini.json        # Bhashini ULCA config & compute schemas
└── traceability.md          # Generated requirement-to-test traceability matrix
```

### Source Code Layout
```text
src/
├── domain/                               # Pure business logic (0 framework/IO imports)
│   ├── __init__.py
│   ├── session.py                        # UserSession, SessionState, LanguageValidator
│   ├── translation.py                    # TranslationRequest, MultilingualResponse
│   └── weather.py                        # WeatherReport, ForecastDay
├── adapters/                             # Isolated external communication & I/O
│   ├── __init__.py
│   ├── bhashini/
│   │   ├── __init__.py
│   │   └── client.py                     # BhashiniPipelineClient (ASR, NMT, TTS)
│   ├── whatsapp/
│   │   ├── __init__.py
│   │   └── client.py                     # WhatsAppClient (send text/audio, media download)
│   ├── weather/
│   │   ├── __init__.py
│   │   └── client.py                     # OpenMeteoClient (geocoding, daily forecast)
│   └── audio/
│       ├── __init__.py
│       └── transcoder.py                 # FFmpeg OGG-to-WAV PCM memory transcoder
└── api/                                  # Presentation & routing layer
    ├── __init__.py
    ├── app.py                            # FastAPI app with CORS & lifecycle
    ├── config.py                         # Settings loaded from environment (Infisical)
    ├── routes/
    │   ├── __init__.py
    │   ├── health.py                     # Health check route
    │   └── webhook.py                    # WhatsApp GET verification & POST event intake
    └── worker.py                         # Async orchestrator connecting Session + Adapters

tests/
├── unit/
│   ├── test_health.py                    # Health check verification
│   ├── test_session_domain.py            # Session state machine & language selection
│   ├── test_bhashini_adapter.py          # Bhashini payload generation & parsing
│   ├── test_weather_adapter.py           # Weather response parsing
│   └── test_audio_transcoder.py          # FFmpeg invocation and format assertions
└── acceptance/
    ├── test_smoke.py                     # App boot sanity
    ├── test_language_selection.py        # US1-AS1, US1-AS2, US1-AS3
    ├── test_translate_flow.py            # US2-AS1, US2-AS2, US2-AS3, US2-AS4
    ├── test_voice_message_flow.py        # US3-AS1, US3-AS2, US3-AS3
    └── test_weather_flow.py              # US4-AS1, US4-AS2, US4-AS3
```

---

## 5. Harness and Verification Plan *(mandatory)*

### Verification Commands
- Inner loop check: `python scripts/harness/verify.py --fast`
- Full verification: `python scripts/harness/verify.py`
- Traceability verification: `python scripts/harness/check_traceability.py --strict`
- Unit tests: `uv run pytest -q tests/unit`
- Acceptance tests: `uv run pytest -q tests/acceptance`

### Test Design Matrix per User Story
| Story | Acceptance Test File | Scenarios Covered | Unit Focus | External Mocks |
|---|---|---|---|---|
| **US1 (P1)** | `tests/acceptance/test_language_selection.py` | `US1-AS1`, `US1-AS2`, `US1-AS3` | `FR-002`, `FR-003`, `FR-004`, `FR-005` | Mock WhatsApp send |
| **US2 (P1)** | `tests/acceptance/test_translate_flow.py` | `US2-AS1`, `US2-AS2`, `US2-AS3`, `US2-AS4` | `FR-006` | Mock Bhashini NMT & ASR |
| **US3 (P1)** | `tests/acceptance/test_voice_message_flow.py` | `US3-AS1`, `US3-AS2`, `US3-AS3` | `FR-007` | Mock Bhashini ASR, NMT, TTS |
| **US4 (P2)** | `tests/acceptance/test_weather_flow.py` | `US4-AS1`, `US4-AS2`, `US4-AS3` | `FR-008` | Mock Open-Meteo & Bhashini NMT |

---

## 6. Ownership, Reuse & Invariants

- **Invariant INV-1 (Single Domain Ownership)**:
  - Session state logic lives exclusively in `src/domain/session.py`.
  - Speech & translation business models live in `src/domain/translation.py`.
  - Weather summarization logic lives in `src/domain/weather.py`.
- **Invariant INV-2 (No Duplicate Logic)**:
  - Bhashini compute API calling logic consolidated into `src/adapters/bhashini/client.py`.
  - FFmpeg process management isolated to `src/adapters/audio/transcoder.py`.
- **Invariant INV-3 (No Business Logic in Presentation)**:
  - `src/api/routes/webhook.py` performs request validation and returns HTTP 200 within 50ms; orchestrator worker computes responses.

---

## 7. Security, Privacy & Rollback

- **Zero Secret Spills**: Secrets (`BHASHINI_API_KEY`, `WHATSAPP_TOKEN`) injected via Infisical at runtime; never logged, written to disk, or printed.
- **Citizen Privacy**: Audio streams and user queries processed in memory; no persistent raw audio storage on local filesystems.
- **Rollback**: One-command revert `git checkout main && git branch -D 001-whatsapp-multilingual-bot`.

---

### Gate G2 — "Design Ready"
- [x] Constitution Check passes without violations
- [x] Contracts (`whatsapp.json`, `bhashini.json`), data model, and test matrix cover every FR and scenario
- [x] Owning modules identified (`src/domain/`, `src/adapters/`, `src/api/`); strict separation enforced
- [x] Security, observability, rollout and rollback documented
- [x] Tech lead approval: Approved by Karthik Kamalakar on 2026-10-11
