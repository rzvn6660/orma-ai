import os
import base64
import email
from unittest.mock import patch, MagicMock
import pytest
import httpx
from google.auth.exceptions import RefreshError

from services.gmail_email_service import (
    get_gmail_config,
    is_gmail_configured,
    build_raw_mime_message,
    send_gmail_message,
    GMAIL_SEND_URL,
    GMAIL_SEND_SCOPE,
)

SAMPLE_CLIENT_ID = "mock-client-id-12345.apps.googleusercontent.com"
SAMPLE_CLIENT_SECRET = "GOCSPX-mock-client-secret-abcde"
SAMPLE_REFRESH_TOKEN = "1//mock-refresh-token-xyz987"
SAMPLE_SENDER_EMAIL = "orma.assistant.qa@gmail.com"
MOCK_ENV = {
    "GMAIL_CLIENT_ID": SAMPLE_CLIENT_ID,
    "GMAIL_CLIENT_SECRET": SAMPLE_CLIENT_SECRET,
    "GMAIL_REFRESH_TOKEN": SAMPLE_REFRESH_TOKEN,
    "GMAIL_SENDER_EMAIL": SAMPLE_SENDER_EMAIL,
    "ENVIRONMENT": "production",
}


def test_mime_construction_and_base64url_encoding():
    """Verifies RFC 2822 MIME structure, recipient, subject, bodies, and base64url encoding."""
    to_email = "recipient@family.com"
    subject = "Verify your ORMA account"
    body_html = "<h1>Welcome to ORMA</h1><p>Your code is <strong>123456</strong></p>"
    body_text = "Welcome to ORMA. Your code is 123456"
    sender_name = "ORMA AI Healthcare"

    raw_b64 = build_raw_mime_message(
        sender_email=SAMPLE_SENDER_EMAIL,
        to_email=to_email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        sender_name=sender_name,
    )

    assert isinstance(raw_b64, str)
    # Decode base64url (add padding if necessary)
    padded = raw_b64 + "=" * (-len(raw_b64) % 4)
    decoded_bytes = base64.urlsafe_b64decode(padded.encode("ascii"))
    parsed = email.message_from_bytes(decoded_bytes)

    assert parsed["Subject"] == subject
    assert parsed["To"] == to_email
    assert parsed["From"] == f"{sender_name} <{SAMPLE_SENDER_EMAIL}>"
    assert parsed.is_multipart()

    payload_parts = parsed.get_payload()
    assert len(payload_parts) == 2
    plain_part = payload_parts[0]
    html_part = payload_parts[1]

    assert plain_part.get_content_type() == "text/plain"
    assert "123456" in plain_part.get_payload(decode=True).decode("utf-8")
    assert html_part.get_content_type() == "text/html"
    assert "<h1>Welcome to ORMA</h1>" in html_part.get_payload(decode=True).decode("utf-8")


def test_is_gmail_configured():
    """Verifies detection of complete vs missing Gmail credentials."""
    with patch.dict(os.environ, MOCK_ENV, clear=True):
        assert is_gmail_configured() is True

    # Missing refresh token
    incomplete_env = dict(MOCK_ENV)
    incomplete_env.pop("GMAIL_REFRESH_TOKEN")
    with patch.dict(os.environ, incomplete_env, clear=True):
        assert is_gmail_configured() is False


def test_token_refresh_and_auth_header():
    """Verifies that Google OAuth Credentials refresh automatically and inject Bearer token."""
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.token = "ya29.fresh_access_token_mock_123"

    def fake_refresh(request):
        mock_creds.valid = True
        mock_creds.expired = False

    mock_creds.refresh.side_effect = fake_refresh

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "gmail_msg_9999", "threadId": "th_1111"}

    with patch.dict(os.environ, MOCK_ENV):
        with patch("services.gmail_email_service.Credentials", return_value=mock_creds):
            with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
                resp = send_gmail_message(
                    to_email="tester@test.com",
                    subject="Test Subject",
                    body_html="<p>Test</p>",
                    body_text="Test",
                )

                assert mock_creds.refresh.called
                assert resp["id"] == "gmail_msg_9999"

                call_args = mock_post.call_args
                url = call_args[0][0]
                headers = call_args[1]["headers"]
                json_body = call_args[1]["json"]

                assert url == GMAIL_SEND_URL
                assert headers["Authorization"] == "Bearer ya29.fresh_access_token_mock_123"
                assert "raw" in json_body


def test_send_gmail_message_success():
    """Verifies successful Gmail API dispatch."""
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.token = "mock_token"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "msg_success_123"}

    with patch.dict(os.environ, MOCK_ENV):
        with patch("services.gmail_email_service._get_authenticated_credentials", return_value=mock_creds):
            with patch("httpx.Client.post", return_value=mock_resp):
                result = send_gmail_message(
                    to_email="test@domain.com",
                    subject="Hello",
                    body_html="<p>Body</p>",
                    body_text="Body",
                )
                assert result["id"] == "msg_success_123"


def test_send_gmail_message_api_http_failure():
    """Verifies handling of Gmail API HTTP errors (e.g., 403 Forbidden)."""
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.token = "mock_token"

    fake_req = httpx.Request("POST", GMAIL_SEND_URL)
    fake_resp = httpx.Response(403, request=fake_req, text='{"error": {"message": "Access Denied"}}')

    with patch.dict(os.environ, MOCK_ENV):
        with patch("services.gmail_email_service._get_authenticated_credentials", return_value=mock_creds):
            with patch("httpx.Client.post", return_value=fake_resp):
                with pytest.raises(RuntimeError) as exc_info:
                    send_gmail_message(
                        to_email="fail@domain.com",
                        subject="Fail",
                        body_html="<p>Fail</p>",
                        body_text="Fail",
                    )
                assert "403" in str(exc_info.value)
                # Ensure client secret is NOT leaked in exception message
                assert SAMPLE_CLIENT_SECRET not in str(exc_info.value)
                assert SAMPLE_REFRESH_TOKEN not in str(exc_info.value)


def test_send_gmail_message_token_refresh_failure():
    """Verifies handling of OAuth RefreshError without leaking secrets."""
    with patch.dict(os.environ, MOCK_ENV):
        with patch(
            "services.gmail_email_service._get_authenticated_credentials",
            side_effect=RefreshError("Invalid grant: token has been expired or revoked"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                send_gmail_message(
                    to_email="test@domain.com",
                    subject="Fail",
                    body_html="<p>Fail</p>",
                    body_text="Fail",
                )
            assert "Gmail authentication refresh failed" in str(exc_info.value)
            assert SAMPLE_REFRESH_TOKEN not in str(exc_info.value)


def test_unconfigured_development_mode_simulates():
    """In development mode without credentials, prints simulation without throwing."""
    dev_env = {"ENVIRONMENT": "development"}
    with patch.dict(os.environ, dev_env, clear=True):
        result = send_gmail_message(
            to_email="dev@local.test",
            subject="Dev Subject",
            body_html="<p>Dev</p>",
            body_text="Dev",
        )
        assert result["status"] == "simulated"


def test_unconfigured_production_mode_raises():
    """In production mode without credentials, raises RuntimeError."""
    prod_env = {"ENVIRONMENT": "production"}
    with patch.dict(os.environ, prod_env, clear=True):
        with pytest.raises(RuntimeError) as exc_info:
            send_gmail_message(
                to_email="user@prod.com",
                subject="Prod Subject",
                body_html="<p>Prod</p>",
                body_text="Prod",
            )
        assert "missing Gmail API credentials in production" in str(exc_info.value)
