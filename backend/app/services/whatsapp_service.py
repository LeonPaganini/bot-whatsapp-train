import json
import logging
from urllib import request

from app.core.config import settings

LOGGER = logging.getLogger(__name__)


class WhatsAppService:
    def send_text(self, to_number: str, text: str) -> None:
        if not settings.whatsapp_token or not settings.whatsapp_phone_number_id:
            LOGGER.warning("WhatsApp credentials not configured")
            return
        url = (
            "https://graph.facebook.com/v20.0/"
            f"{settings.whatsapp_phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": text},
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {settings.whatsapp_token}")
        req.add_header("Content-Type", "application/json")
        try:
            with request.urlopen(req) as response:
                response.read()
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Erro ao enviar mensagem WhatsApp: %s", exc)
