import os
import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any

import httpx
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

logger = logging.getLogger(__name__)

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
TOKEN_URI = "https://oauth2.googleapis.com/token"

# In-memory cached credentials instance to reuse valid access tokens
_cached_credentials: Optional[Credentials] = None


def get_gmail_config() -> Dict[str, str]:
    """
    Retrieves Gmail API credentials from environment variables.
    NEVER logs or prints secret values.
    """
    return {
        "client_id": os.environ.get("GMAIL_CLIENT_ID", "").strip(),
        "client_secret": os.environ.get("GMAIL_CLIENT_SECRET", "").strip(),
        "refresh_token": os.environ.get("GMAIL_REFRESH_TOKEN", "").strip(),
        "sender_email": os.environ.get("GMAIL_SENDER_EMAIL", "").strip(),
    }


def is_gmail_configured() -> bool:
    """Checks whether all required Gmail API credentials are present."""
    config = get_gmail_config()
    return bool(
        config["client_id"]
        and config["client_secret"]
        and config["refresh_token"]
        and config["sender_email"]
    )


def _get_authenticated_credentials(config: Dict[str, str]) -> Credentials:
    """
    Returns a valid Google OAuth2 Credentials object, refreshing the access
    token automatically if needed.
    """
    global _cached_credentials

    # Check if cached credentials match current env credentials
    if (
        _cached_credentials is not None
        and _cached_credentials.client_id == config["client_id"]
        and _cached_credentials.client_secret == config["client_secret"]
        and _cached_credentials.refresh_token == config["refresh_token"]
    ):
        creds = _cached_credentials
    else:
        creds = Credentials(
            token=None,
            refresh_token=config["refresh_token"],
            token_uri=TOKEN_URI,
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            scopes=[GMAIL_SEND_SCOPE],
        )
        _cached_credentials = creds

    # Refresh if expired or token is missing
    if not creds.valid or creds.expired:
        creds.refresh(Request())

    return creds


def build_raw_mime_message(
    sender_email: str,
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str,
    sender_name: str = "ORMA AI",
) -> str:
    """
    Constructs a multipart alternative MIME message and encodes it
    to URL-safe Base64 as required by the Gmail API.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    msg["To"] = to_email

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    raw_bytes = msg.as_bytes()
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8")


def send_gmail_message(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str,
    sender_name: str = "ORMA AI",
) -> Dict[str, Any]:
    """
    Sends an email using the Gmail API over HTTPS (port 443).
    Adheres strictly to the least-privilege gmail.send scope.

    In development mode, if credentials are not configured, prints
    the email content to server stdout without throwing.

    Raises RuntimeError if delivery fails in production.
    """
    config = get_gmail_config()
    env_mode = os.environ.get("ENVIRONMENT", os.environ.get("ENV", "development")).strip().lower()

    if not is_gmail_configured():
        if env_mode == "production":
            logger.error("[GMAIL-API] Gmail API credentials missing in production environment. Email cannot be delivered.")
            raise RuntimeError("Email service unavailable: missing Gmail API credentials in production.")
        else:
            logger.warning("[GMAIL-API] Development mode — Gmail API credentials unset. Simulating email dispatch.")
            return {"status": "simulated", "to": to_email, "subject": subject}

    try:
        creds = _get_authenticated_credentials(config)
        access_token = creds.token
        if not access_token:
            raise RuntimeError("Failed to obtain a valid access token from Google OAuth2.")

        raw_payload = build_raw_mime_message(
            sender_email=config["sender_email"],
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            sender_name=sender_name,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                GMAIL_SEND_URL,
                headers=headers,
                json={"raw": raw_payload},
            )

        if response.status_code != 200:
            logger.error(
                f"[GMAIL-API] Message send failed with HTTP {response.status_code}: {response.text[:300]}"
            )
            response.raise_for_status()

        resp_data = response.json()
        logger.info(f"[GMAIL-API] Email delivered to recipient via Gmail API (id={resp_data.get('id', 'ok')})")
        return resp_data

    except RefreshError as e:
        logger.error(f"[GMAIL-API] Token refresh failed: {type(e).__name__} ({str(e)})")
        raise RuntimeError(f"Gmail authentication refresh failed: {type(e).__name__}") from e
    except httpx.HTTPStatusError as e:
        logger.error(f"[GMAIL-API] Gmail API HTTP error {e.response.status_code}: {e.response.text[:200]}")
        raise RuntimeError(f"Gmail API delivery rejected: HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        logger.error(f"[GMAIL-API] Network connectivity error to Gmail API: {type(e).__name__}")
        raise RuntimeError(f"Gmail API network error: {type(e).__name__}") from e
    except Exception as e:
        logger.error(f"[GMAIL-API] Unexpected error during email dispatch: {type(e).__name__}")
        raise
