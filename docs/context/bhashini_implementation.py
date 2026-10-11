import os
import io
import base64
import logging
import asyncio
import subprocess
import httpx
from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bhashini-whatsapp-poc")

# Environment Configuration
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID")
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY")
BHASHINI_PIPELINE_ID = os.getenv("BHASHINI_PIPELINE_ID", "64392f96daac500b55c543d0")

BHASHINI_CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
META_GRAPH_BASE_URL = "https://graph.facebook.com/v21.0"

app = FastAPI(title="Bhashini WhatsApp Middleware")


class BhashiniPipelineClient:
    """Manages dynamic auth handshake and compute execution for Bhashini APIs."""

    def __init__(self, user_id: str, api_key: str, pipeline_id: str):
        self.user_id = user_id
        self.api_key = api_key
        self.pipeline_id = pipeline_id

    async def get_pipeline_endpoint(
        self,
        client: httpx.AsyncClient,
        tasks: list,
    ) -> dict:
        headers = {
            "userID": self.user_id,
            "ulcaApiKey": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "pipelineTasks": tasks,
            "pipelineRequestConfig": {"pipelineId": self.pipeline_id},
        }
        response = await client.post(BHASHINI_CONFIG_URL, json=payload, headers=headers, timeout=12.0)
        if response.status_code != 200:
            logger.error(f"Bhashini Config Failed [{response.status_code}]: {response.text}")
            raise HTTPException(status_code=502, detail="Failed to initialize Bhashini pipeline configuration")
        return response.json()

    async def run_asr_pipeline(
        self,
        client: httpx.AsyncClient,
        audio_base64: str,
        source_language: str = "hi",
    ) -> str:
        """Executes speech-to-text transcription on raw base64 16kHz audio."""
        config_tasks = [
            {
                "taskType": "asr",
                "config": {"language": {"sourceLanguage": source_language}},
            }
        ]
        config_data = await self.get_pipeline_endpoint(client, config_tasks)

        endpoint_info = config_data["pipelineInferenceAPIEndPoint"]
        callback_url = endpoint_info["callbackUrl"]
        auth_header_name = endpoint_info["inferenceApiKey"]["name"]
        auth_header_val = endpoint_info["inferenceApiKey"]["value"]
        service_id = config_data["pipelineResponseConfig"][0]["config"][0]["serviceId"]

        compute_headers = {
            auth_header_name: auth_header_val,
            "Content-Type": "application/json",
        }
        compute_payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {"sourceLanguage": source_language},
                        "serviceId": service_id,
                        "audioFormat": "wav",
                        "samplingRate": 16000,
                    },
                }
            ],
            "inputData": {
                "audio": [{"audioContent": audio_base64}]
            },
        }

        compute_res = await client.post(
            callback_url,
            json=compute_payload,
            headers=compute_headers,
            timeout=25.0,
        )
        if compute_res.status_code != 200:
            logger.error(f"ASR Compute Failed [{compute_res.status_code}]: {compute_res.text}")
            raise HTTPException(status_code=502, detail="Bhashini ASR computation failed")

        data = compute_res.json()
        transcript = data["pipelineResponse"][0]["output"][0]["source"]
        return transcript

    async def run_translation_and_tts_pipeline(
        self,
        client: httpx.AsyncClient,
        text_content: str,
        source_lang: str = "en",
        target_lang: str = "hi",
    ) -> tuple[str, str]:
        """Translates text and returns target translated text + synthesized base64 audio."""
        config_tasks = [
            {
                "taskType": "translation",
                "config": {"language": {"sourceLanguage": source_lang, "targetLanguage": target_lang}},
            },
            {
                "taskType": "tts",
                "config": {"language": {"sourceLanguage": target_lang}},
            },
        ]
        config_data = await self.get_pipeline_endpoint(client, config_tasks)

        endpoint_info = config_data["pipelineInferenceAPIEndPoint"]
        callback_url = endpoint_info["callbackUrl"]
        auth_header_name = endpoint_info["inferenceApiKey"]["name"]
        auth_header_val = endpoint_info["inferenceApiKey"]["value"]

        nmt_service_id = config_data["pipelineResponseConfig"][0]["config"][0]["serviceId"]
        tts_service_id = config_data["pipelineResponseConfig"][1]["config"][0]["serviceId"]

        compute_headers = {
            auth_header_name: auth_header_val,
            "Content-Type": "application/json",
        }
        compute_payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {"sourceLanguage": source_lang, "targetLanguage": target_lang},
                        "serviceId": nmt_service_id,
                    },
                },
                {
                    "taskType": "tts",
                    "config": {
                        "language": {"sourceLanguage": target_lang},
                        "serviceId": tts_service_id,
                        "gender": "female",
                    },
                },
            ],
            "inputData": {
                "input": [{"source": text_content}]
            },
        }

        compute_res = await client.post(
            callback_url,
            json=compute_payload,
            headers=compute_headers,
            timeout=25.0,
        )
        if compute_res.status_code != 200:
            logger.error(f"NMT+TTS Compute Failed [{compute_res.status_code}]: {compute_res.text}")
            raise HTTPException(status_code=502, detail="Bhashini NMT+TTS pipeline failed")

        data = compute_res.json()
        translated_text = data["pipelineResponse"][0]["output"][0]["target"]
        synthesized_audio_base64 = data["pipelineResponse"][1]["audio"][0]["audioContent"]
        return translated_text, synthesized_audio_base64


bhashini_client = BhashiniPipelineClient(
    user_id=BHASHINI_USER_ID,
    api_key=BHASHINI_API_KEY,
    pipeline_id=BHASHINI_PIPELINE_ID,
)


def transcode_ogg_to_wav_pcm(ogg_bytes: bytes) -> bytes:
    """Converts OGG Opus audio binary stream to 16kHz Mono 16-bit PCM WAV using FFmpeg."""
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", "pipe:0",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        "pipe:1",
    ]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    wav_output, stderr = process.communicate(input=ogg_bytes)
    if process.returncode != 0:
        logger.error(f"FFmpeg transcode error: {stderr.decode('utf-8')}")
        raise RuntimeError("Audio transcoding pipeline failure")
    return wav_output


async def download_whatsapp_media(media_id: str, client: httpx.AsyncClient) -> bytes:
    """Retrieves temporary media URL and streams raw binary from Meta Graph API."""
    meta_headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    url_req = await client.get(f"{META_GRAPH_BASE_URL}/{media_id}", headers=meta_headers, timeout=10.0)
    if url_req.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to retrieve WhatsApp media link")

    download_url = url_req.json().get("url")
    bin_req = await client.get(download_url, headers=meta_headers, timeout=20.0)
    if bin_req.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to stream WhatsApp media binary")
    return bin_req.content


async def send_whatsapp_text(recipient_phone: str, message: str, client: httpx.AsyncClient):
    """Dispatches standard UTF-8 text message via WhatsApp Business API."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    await client.post(
        f"{META_GRAPH_BASE_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages",
        json=payload,
        headers=headers,
        timeout=10.0,
    )


async def send_whatsapp_audio(recipient_phone: str, audio_bytes: bytes, client: httpx.AsyncClient):
    """Uploads synthesized audio to WhatsApp Media Storage and dispatches as voice message."""
    upload_url = f"{META_GRAPH_BASE_URL}/{WHATSAPP_PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {
        "file": ("response.wav", audio_bytes, "audio/wav"),
    }
    data = {
        "messaging_product": "whatsapp",
        "type": "audio/wav",
    }
    up_res = await client.post(upload_url, headers=headers, data=data, files=files, timeout=20.0)
    if up_res.status_code != 200:
        logger.error(f"WhatsApp Media Upload Failed: {up_res.text}")
        return

    media_id = up_res.json()["id"]

    msg_payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "audio",
        "audio": {"id": media_id},
    }
    msg_headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    await client.post(
        f"{META_GRAPH_BASE_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages",
        json=msg_payload,
        headers=msg_headers,
        timeout=10.0,
    )


def execute_business_engine(english_query: str) -> str:
    """Simulates domain business logic and intent routing."""
    query_lower = english_query.lower()
    if "price" in query_lower or "rate" in query_lower:
        return "Today's Mandi rate for wheat is 2,275 Rupees per quintal, and mustard is 5,400 Rupees per quintal."
    elif "weather" in query_lower or "rain" in query_lower:
        return "Expect light scattered showers over the next 48 hours. Postpone field irrigation accordingly."
    else:
        return f"Your request regarding '{english_query}' has been logged. A regional representative will follow up."


async def process_voice_interaction(sender_id: str, media_id: str):
    """Asynchronous worker resolving speech transcription, translation, and voice synthesis."""
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Processing inbound voice message for recipient: {sender_id}")
            ogg_audio = await download_whatsapp_media(media_id, client)

            loop = asyncio.get_running_loop()
            wav_bytes = await loop.run_in_executor(None, transcode_ogg_to_wav_pcm, ogg_audio)
            audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")

            vernacular_transcript = await bhashini_client.run_asr_pipeline(
                client, audio_base64=audio_base64, source_language="hi"
            )
            logger.info(f"Recognized Speech Transcript: {vernacular_transcript}")

            english_response = execute_business_engine(vernacular_transcript)

            translated_reply, synth_audio_base64 = await bhashini_client.run_translation_and_tts_pipeline(
                client,
                text_content=english_response,
                source_lang="en",
                target_lang="hi",
            )

            synth_audio_bytes = base64.b64decode(synth_audio_base64)
            await send_whatsapp_text(sender_id, f"नतीजा (Result): {translated_reply}", client)
            await send_whatsapp_audio(sender_id, synth_audio_bytes, client)
            logger.info(f"Completed interaction flow for {sender_id}")

        except Exception as err:
            logger.exception(f"Error handling interaction: {err}")
            error_fallback = "माफ़ कीजिये, आपकी आवाज़ संसाधित करने में समस्या हुई। कृपया पुनः प्रयास करें।"
            await send_whatsapp_text(sender_id, error_fallback, client)


@app.get("/webhook")
async def verify_webhook(request: Request):
    """Handles verification handshake from Meta Webhook console."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain", status_code=status.HTTP_200_OK)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")


@app.post("/webhook")
async def receive_whatsapp_event(request: Request, background_tasks: BackgroundTasks):
    """Ingests incoming WhatsApp events and offloads processing to background tasks."""
    body = await request.json()

    if body.get("object") != "whatsapp_business_account":
        return Response(content="ignored", status_code=status.HTTP_200_OK)

    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                sender_id = msg.get("from")
                msg_type = msg.get("type")

                if msg_type == "audio":
                    media_id = msg["audio"]["id"]
                    background_tasks.add_task(process_voice_interaction, sender_id, media_id)
                elif msg_type == "text":
                    text_content = msg["text"]["body"]
                    logger.info(f"Received text message: '{text_content}' from {sender_id}")

    return Response(content="EVENT_RECEIVED", status_code=status.HTTP_200_OK)