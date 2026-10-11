# Quickstart & Verification: WhatsApp Multilingual Bot

**Feature**: `001-whatsapp-multilingual-bot`  
**Date**: 2026-10-11

---

## 1. Prerequisites
- Python 3.12+ with `uv`
- Infisical CLI (`infisical login` with project `bhashini-poc`)
- FFmpeg installed locally (for audio transcoding)

---

## 2. Running Locally with Infisical Secrets

```bash
# Sync dependencies
uv sync

# Run the FastAPI server locally injecting credentials from Infisical:
infisical run -- uv run uvicorn src.api.app:app --reload --port 8000
```

---

## 3. Running Verification Suite

```bash
# Fast inner loop checks (format, lint, unit tests)
python scripts/harness/verify.py --fast

# Full verification (unit tests, acceptance tests, traceability, test integrity)
python scripts/harness/verify.py
```

---

## 4. Testing Webhook with ngrok / Local Tunnel

```bash
# Expose port 8000 to internet
ngrok http 8000

# Webhook Callback URL: https://<ngrok-id>.ngrok-free.app/webhook
# Verify Token: Value stored in Infisical WHATSAPP_VERIFY_TOKEN
```
