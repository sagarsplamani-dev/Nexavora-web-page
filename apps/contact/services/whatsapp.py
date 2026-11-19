import json
import logging
import re
from dataclasses import dataclass, field
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone

from apps.contact.models import Enquiry


logger = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 8
MAX_RESPONSE_BYTES = 65536
E164_DIGITS_RE = re.compile(r"^[1-9]\d{7,14}$")
GRAPH_VERSION_RE = re.compile(r"^v\d+\.\d+$")


class WhatsAppConfigurationError(Exception):
    def __init__(self, setting_names: Sequence[str]):
        self.setting_names = tuple(setting_names)
        super().__init__("WhatsApp configuration is missing or invalid.")


class WhatsAppAPIError(Exception):
    def __init__(self, code: str, *, outcome_unknown: bool = False):
        self.code = code
        self.outcome_unknown = outcome_unknown
        super().__init__(code)


@dataclass(frozen=True)
class WhatsAppConfig:
    access_token: str = field(repr=False)
    phone_number_id: str
    business_account_id: str
    admin_phone: str
    graph_api_version: str


def get_whatsapp_config() -> WhatsAppConfig:
    values = {
        "WHATSAPP_ACCESS_TOKEN": settings.WHATSAPP_ACCESS_TOKEN,
        "WHATSAPP_PHONE_NUMBER_ID": settings.WHATSAPP_PHONE_NUMBER_ID,
        "WHATSAPP_BUSINESS_ACCOUNT_ID": settings.WHATSAPP_BUSINESS_ACCOUNT_ID,
        "WHATSAPP_ADMIN_PHONE": settings.WHATSAPP_ADMIN_PHONE,
        "WHATSAPP_GRAPH_API_VERSION": settings.WHATSAPP_GRAPH_API_VERSION,
    }
    missing = [name for name, value in values.items() if not value]
    invalid = [
        name
        for name, value in values.items()
        if value and value.casefold().startswith("replace-with-")
    ]
    if values["WHATSAPP_PHONE_NUMBER_ID"] and not values[
        "WHATSAPP_PHONE_NUMBER_ID"
    ].isdigit():
        invalid.append("WHATSAPP_PHONE_NUMBER_ID")
    if values["WHATSAPP_BUSINESS_ACCOUNT_ID"] and not values[
        "WHATSAPP_BUSINESS_ACCOUNT_ID"
    ].isdigit():
        invalid.append("WHATSAPP_BUSINESS_ACCOUNT_ID")
    if values["WHATSAPP_ADMIN_PHONE"] and not E164_DIGITS_RE.fullmatch(
        values["WHATSAPP_ADMIN_PHONE"]
    ):
        invalid.append("WHATSAPP_ADMIN_PHONE")
    if values["WHATSAPP_GRAPH_API_VERSION"] and not GRAPH_VERSION_RE.fullmatch(
        values["WHATSAPP_GRAPH_API_VERSION"]
    ):
        invalid.append("WHATSAPP_GRAPH_API_VERSION")

    if missing or invalid:
        raise WhatsAppConfigurationError((*missing, *invalid))

    return WhatsAppConfig(
        access_token=values["WHATSAPP_ACCESS_TOKEN"],
        phone_number_id=values["WHATSAPP_PHONE_NUMBER_ID"],
        business_account_id=values["WHATSAPP_BUSINESS_ACCOUNT_ID"],
        admin_phone=values["WHATSAPP_ADMIN_PHONE"],
        graph_api_version=values["WHATSAPP_GRAPH_API_VERSION"],
    )


def _graph_error_code(response_body: bytes) -> str:
    try:
        payload = json.loads(response_body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "invalid_response"
    if not isinstance(payload, dict):
        return "invalid_response"
    error = payload.get("error")
    code = error.get("code") if isinstance(error, dict) else None
    if isinstance(code, int):
        return f"graph_{code}"
    return "api_error"


def send_template_message(
    template_name: str,
    language_code: str,
    body_parameters: Sequence[str] = (),
) -> str:
    config = get_whatsapp_config()
    components = []
    if body_parameters:
        components.append(
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": parameter}
                    for parameter in body_parameters
                ],
            }
        )
    template = {
        "name": template_name,
        "language": {"code": language_code},
    }
    if components:
        template["components"] = components
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": config.admin_phone,
        "type": "template",
        "template": template,
    }
    request = Request(
        (
            f"https://graph.facebook.com/{config.graph_api_version}/"
            f"{config.phone_number_id}/messages"
        ),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            response_body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        error_code = _graph_error_code(error.read(MAX_RESPONSE_BYTES))
        raise WhatsAppAPIError(
            f"http_{error.code}_{error_code}",
            outcome_unknown=error.code >= 500,
        ) from None
    except (TimeoutError, URLError, OSError):
        raise WhatsAppAPIError("network_error", outcome_unknown=True) from None

    if len(response_body) > MAX_RESPONSE_BYTES:
        raise WhatsAppAPIError("response_too_large", outcome_unknown=True)
    try:
        response_data = json.loads(response_body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise WhatsAppAPIError("invalid_response", outcome_unknown=True) from None

    if not isinstance(response_data, dict):
        raise WhatsAppAPIError("invalid_response", outcome_unknown=True)
    if "error" in response_data:
        raise WhatsAppAPIError(_graph_error_code(response_body))

    messages = response_data.get("messages")
    if not isinstance(messages, list) or not messages or not isinstance(messages[0], dict):
        raise WhatsAppAPIError("invalid_response", outcome_unknown=True)
    message_id = messages[0].get("id")
    if not isinstance(message_id, str) or not message_id:
        raise WhatsAppAPIError("invalid_response", outcome_unknown=True)
    return message_id


def _enquiry_template_parameters(enquiry: Enquiry) -> list[str]:
    category = enquiry.course or enquiry.subject or enquiry.get_kind_display()
    message = enquiry.message.strip()
    if len(message) > 500:
        message = f"{message[:497]}..."
    submitted_at = timezone.localtime(enquiry.created_at).strftime("%Y-%m-%d %H:%M %Z")
    return [
        str(enquiry.pk),
        category,
        enquiry.name,
        enquiry.email,
        enquiry.phone or "Not provided",
        message or "No message provided",
        submitted_at,
    ]


def notify_enquiry(enquiry: Enquiry) -> None:
    claimed = Enquiry.objects.filter(
        pk=enquiry.pk,
        whatsapp_status=Enquiry.WhatsAppStatus.PENDING,
    ).update(
        whatsapp_status=Enquiry.WhatsAppStatus.SENDING,
        whatsapp_attempted_at=timezone.now(),
        whatsapp_error_code="",
    )
    if not claimed:
        return

    try:
        get_whatsapp_config()
    except WhatsAppConfigurationError as error:
        _mark_failed(enquiry.pk, "configuration_error")
        logger.error(
            "WhatsApp notification configuration error for enquiry_id=%s missing_or_invalid_settings=%s",
            enquiry.pk,
            ",".join(error.setting_names),
        )
        return

    template_name = settings.WHATSAPP_NOTIFICATION_TEMPLATE
    language_code = settings.WHATSAPP_TEMPLATE_LANGUAGE
    if not template_name or template_name.casefold().startswith("replace-with-"):
        _mark_failed(enquiry.pk, "missing_template")
        logger.error(
            "WhatsApp notification configuration error for enquiry_id=%s missing_setting=WHATSAPP_NOTIFICATION_TEMPLATE",
            enquiry.pk,
        )
        return

    try:
        message_id = send_template_message(
            template_name,
            language_code,
            _enquiry_template_parameters(enquiry),
        )
    except WhatsAppConfigurationError as error:
        _mark_failed(enquiry.pk, "configuration_error")
        logger.error(
            "WhatsApp notification configuration error for enquiry_id=%s missing_or_invalid_settings=%s",
            enquiry.pk,
            ",".join(error.setting_names),
        )
    except WhatsAppAPIError as error:
        status = (
            Enquiry.WhatsAppStatus.UNKNOWN
            if error.outcome_unknown
            else Enquiry.WhatsAppStatus.FAILED
        )
        Enquiry.objects.filter(pk=enquiry.pk).update(
            whatsapp_status=status,
            whatsapp_error_code=error.code[:64],
        )
        logger.warning(
            "WhatsApp notification %s for enquiry_id=%s error_code=%s",
            status,
            enquiry.pk,
            error.code,
        )
    else:
        Enquiry.objects.filter(pk=enquiry.pk).update(
            whatsapp_status=Enquiry.WhatsAppStatus.ACCEPTED,
            whatsapp_message_id=message_id[:255],
            whatsapp_error_code="",
        )
        logger.info(
            "WhatsApp notification accepted by Meta for enquiry_id=%s message_id=%s",
            enquiry.pk,
            message_id,
        )


def _mark_failed(enquiry_id: int, error_code: str) -> None:
    Enquiry.objects.filter(pk=enquiry_id).update(
        whatsapp_status=Enquiry.WhatsAppStatus.FAILED,
        whatsapp_error_code=error_code,
    )
