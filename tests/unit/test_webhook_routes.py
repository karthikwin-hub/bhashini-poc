"""Unit tests for Meta WhatsApp webhook endpoints.

Covers:
- FR-001: WhatsApp Business Cloud API integration.
- FR-010: Webhook verification and logging.
"""

from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_webhook_verification_success():
    """Verify Meta handshake returns hub.challenge when token matches."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "bhashini_verify_token_secure",
        "hub.challenge": "1158201444",
    }
    response = client.get("/webhook", params=params)
    assert response.status_code == 200
    assert response.text == "1158201444"


def test_webhook_verification_failure():
    """Verify handshake returns HTTP 403 on invalid token."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "1158201444",
    }
    response = client.get("/webhook", params=params)
    assert response.status_code == 403


def test_webhook_post_event_ingestion():
    """Verify inbound WhatsApp event payload returns 200 EVENT_RECEIVED immediately."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550269999",
                                "phone_number_id": "1234567890",
                            },
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.HBgLM...",
                                    "timestamp": "1739260800",
                                    "text": {"body": "Hi"},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "EVENT_RECEIVED"}
