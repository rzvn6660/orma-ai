import os
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

def verify_google_id_token(token_str: str) -> dict:
    """
    Verifies a Google ID Token (JWT) issued by Google's OAuth 2.0 authentication service.
    
    Returns verified payload dict containing:
      - email: verified email address
      - email_verified: boolean
      - sub: Google unique User ID
      - name: full name (if available)
    
    Raises ValueError if verification fails.
    """
    if not token_str:
        raise ValueError("No ID token provided.")

    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip() or None
    env_mode = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()
    
    if env_mode == "production" and not client_id:
        raise ValueError("Google authentication unavailable: GOOGLE_CLIENT_ID is not configured in production.")

    # 1. Primary verification using official google-auth library
    try:
        id_info = id_token.verify_oauth2_token(
            token_str, 
            google_requests.Request(), 
            audience=client_id
        )

        # Check issuer claim
        if id_info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Invalid issuer claim in Google ID token.")

        # Check email verified
        if not id_info.get("email_verified"):
            raise ValueError("Google email is not verified.")

        return {
            "email": id_info["email"],
            "sub": id_info["sub"],
            "name": id_info.get("name") or id_info.get("given_name") or id_info["email"].split("@")[0],
            "email_verified": True
        }
    except Exception as primary_err:
        # If primary verification fails due to explicit audience mismatch or validation error
        if "audience" in str(primary_err).lower() or "token has expired" in str(primary_err).lower():
            raise ValueError(f"Google ID token validation failed: {str(primary_err)}")

        # 2. Secondary verification fallback via Google Tokeninfo endpoint
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token_str}")
                if resp.status_code == 200:
                    info = resp.json()
                    
                    if info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
                        raise ValueError("Invalid issuer from Google tokeninfo.")

                    if client_id and info.get("aud") != client_id:
                        raise ValueError("Audience mismatch in Google tokeninfo.")
                    elif env_mode == "production" and not client_id:
                        raise ValueError("Audience validation required in production.")

                    if info.get("email_verified") not in [True, "true", "True"]:
                        raise ValueError("Google email is not verified.")

                    return {
                        "email": info["email"],
                        "sub": info["sub"],
                        "name": info.get("name") or info.get("given_name") or info["email"].split("@")[0],
                        "email_verified": True
                    }
        except Exception:
            pass

        raise ValueError(f"Google token verification failed: {str(primary_err)}")
