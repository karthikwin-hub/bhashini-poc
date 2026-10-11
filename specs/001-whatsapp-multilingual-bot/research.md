# Research & Technical Decisions: WhatsApp Multilingual Bot

**Feature**: `001-whatsapp-multilingual-bot`  
**Date**: 2026-10-11

---

## 1. Bhashini ULCA / Dhruva Integration Architecture

### Handshake & Compute Pattern
Bhashini models operate under a two-phase compute pattern:
1. **Config Handshake**: Call `POST https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline` with `userID`, `ulcaApiKey`, and requested pipeline tasks (`asr`, `translation`, `tts`).
2. **Inference Compute**: Response yields:
   - `pipelineInferenceAPIEndPoint.callbackUrl` (dynamic compute cluster endpoint)
   - `pipelineInferenceAPIEndPoint.inferenceApiKey` (dynamic auth header and secret token)
   - `pipelineResponseConfig[].config[].serviceId` (service ID for each model checkpoint)
3. **Execution**: Call `callbackUrl` with the assigned service ID, base64 audio/text payload, and language codes.

### Language Code Mapping for Bhashini
| Language | ISO Code | Bhashini Source/Target Code | ASR Support | NMT Support | TTS Support |
|---|---|---|---|---|---|
| English | `en` | `en` | Yes | Yes | Yes |
| Hindi | `hi` | `hi` | Yes | Yes | Yes |
| Telugu | `te` | `te` | Yes | Yes | Yes |
| Bengali | `bn` | `bn` | Yes | Yes | Yes |
| Tamil | `ta` | `ta` | Yes | Yes | Yes |
| Konkani | `kok` | `gom` / `kok` | Yes | Yes | Yes |

---

## 2. WhatsApp Cloud API Integration (Meta Graph API v21.0)

### Webhook Protocol
- **Verification (`GET /webhook`)**: Validates `hub.mode == 'subscribe'` and `hub.verify_token == WHATSAPP_VERIFY_TOKEN`, replying with `hub.challenge`.
- **Event Ingestion (`POST /webhook`)**: Must return HTTP 200 within 5.0 seconds to prevent Meta retries. Heavy processing is dispatched to background workers (`FastAPI.BackgroundTasks` or async task worker).
- **Outbound Dispatch**:
  - Text: `POST https://graph.facebook.com/v21.0/{phone_number_id}/messages`
  - Audio: `POST https://graph.facebook.com/v21.0/{phone_number_id}/media` (`audio/wav`) -> message with `{"type": "audio", "audio": {"id": media_id}}`.

---

## 3. Audio Transcoding Protocol

- Incoming WhatsApp voice notes are streamed as `audio/ogg; codecs=opus`.
- Bhashini ASR models expect 16,000 Hz, 16-bit Mono Linear PCM WAV.
- Solution: Subprocess piping with `ffmpeg -hide_banner -loglevel error -i pipe:0 -acodec pcm_s16le -ac 1 -ar 16000 -f wav pipe:1` converts streams in memory without writing temporary files to disk.

---

## 4. Weather Forecasting API (Open-Meteo)

- Open-source, no API keys required, reliable global coverage with India high-resolution models.
- **Geocoding**: `https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1` resolves text town/city names to `(latitude, longitude)`.
- **Forecast**: `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum&timezone=auto` provides today and tomorrow daily metrics.
