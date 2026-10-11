# Project Rules

## 1. Secrets & Environment Management (Mandatory)
- **Infisical Project**: All credentials, tokens, and environment variables must be stored in Infisical under the project **`bhashini-poc`**.
- **No Local Storage**: Never store secrets in `.env` files, config files, or local storage. This application is developed and deployed across multiple machines.
- **Runtime Injection**: Inject environment variables at runtime using the Infisical CLI:
  ```bash
  infisical run -- <command>
  # e.g. infisical run -- uv run uvicorn src.api.app:app --reload --port 8000
  ```
- **Secret Setting via CLI**:
  ```bash
  infisical secrets set KEY=VALUE --env dev
  ```

## 2. Glossary
| Term | Meaning in this project |
|---|---|
| **ULCA** | Universal Language Contribution Architecture — MeitY platform for dataset and model orchestration. |
| **Dhruva** | Unified API Gateway for Bhashini model inference (ASR, NMT, TTS). |
| **ASR** | Automatic Speech Recognition (speech-to-text transcription). |
| **NMT** | Neural Machine Translation (text translation between Indic languages and English). |
| **TTS** | Text-to-Speech (audio voice synthesis). |
| **DPI** | Digital Public Infrastructure (India's open public digital infrastructure). |

## 3. Project Invariants
- Audio payloads for Bhashini ASR must be transcoded to 16kHz Mono 16-bit PCM WAV.
- External API calls to Bhashini and WhatsApp must only be performed through adapters (`src/adapters/`).
- Webhook routes must acknowledge requests within 5 seconds to satisfy Meta WhatsApp timeout SLAs.
