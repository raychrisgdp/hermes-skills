#!/usr/bin/env python3
"""Google Docs OAuth2 setup for Hermes Agent — self-contained in this skill.

Commands
--------
  setup.py --check                          Is auth valid?  exit 0 = yes
  setup.py --client-secret /path/to.json    Store client_secret
  setup.py --auth-url                       Print auth URL for user to visit
  setup.py --auth-code CODE_OR_URL          Exchange code → token
  setup.py --revoke                         Delete stored token
"""

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path

HERMES_HOME = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
TOKEN_PATH = HERMES_HOME / "google_token.json"
CLIENT_SECRET_PATH = HERMES_HOME / "google_client_secret.json"
PENDING_PATH = HERMES_HOME / "google_oauth_pending.json"

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

REDIRECT_URI = "http://localhost:1"


# ── helpers ────────────────────────────────────────────

def _ensure_deps():
    try:
        import google_auth_oauthlib  # noqa: F401
        import googleapiclient.discovery  # noqa: F401
    except ImportError:
        print("Installing Google API dependencies…", file=sys.stderr)
        import subprocess
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q",
             "google-auth-oauthlib", "google-api-python-client"]
        )


def _load_pending() -> dict:
    if not PENDING_PATH.exists():
        print("ERROR: No pending OAuth session. Run --auth-url first.", file=sys.stderr)
        sys.exit(1)
    return json.loads(PENDING_PATH.read_text())


# ── commands ───────────────────────────────────────────

def check_auth():
    _ensure_deps()
    has_secret = CLIENT_SECRET_PATH.exists()
    if not TOKEN_PATH.exists():
        if not has_secret:
            print("NOT_AUTHENTICATED")
            print("No client secret found.")
            print("You need OAuth credentials from Google Cloud Console.")
            print(f"  1. Create a GCP project → enable Docs API + Drive API")
            print(f"  2. Create an OAuth client ID (type: Desktop app)")
            print(f"  3. Download the JSON and run:")
            print(f"     setup.py --client-secret /path/to/client_secret.json")
            print(f"  4. Then run: setup.py --auth-url")
            print(f"See references/auth-and-setup.md for full instructions.")
        else:
            print("NOT_AUTHENTICATED")
            print(f"Client secret exists at {CLIENT_SECRET_PATH}")
            print("Run: setup.py --auth-url")
        return False
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    except Exception as e:
        print(f"TOKEN_CORRUPT: {e}")
        return False
    if creds.valid:
        print("AUTHENTICATED")
        if not has_secret:
            print("NOTE: client secret not found — token refresh will fail when access token expires.")
            print(f"      Store it with: setup.py --client-secret /path/to/client_secret.json")
        return True
    if creds.expired and creds.refresh_token:
        if not has_secret:
            print("REFRESH_FAILED")
            print("Token expired and no client secret to refresh it.")
            print(f"  1. Download OAuth client JSON from Cloud Console → APIs → Credentials")
            print(f"  2. Run: setup.py --client-secret /path/to/client_secret.json")
            print(f"  3. Run: setup.py --check  (to retry refresh)")
            print(f"Or revoke and re-auth from scratch:")
            print(f"  setup.py --revoke && setup.py --auth-url")
            return False
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
            print("AUTHENTICATED (refreshed)")
            return True
        except Exception as e:
            print(f"REFRESH_FAILED: {e}")
            print("Try revoking and re-authenticating:")
            print(f"  setup.py --revoke")
            print(f"  setup.py --auth-url")
            return False
    print("TOKEN_INVALID")
    if not has_secret:
        print("No client secret found — cannot re-authenticate.")
        print(f"  1. Download OAuth client JSON from Cloud Console → APIs → Credentials")
        print(f"  2. Run: setup.py --client-secret /path/to/client_secret.json")
    else:
        print("Run: setup.py --revoke && setup.py --auth-url")
    return False


def store_client_secret(path: str):
    src = Path(path).expanduser().resolve()
    if not src.exists():
        print(f"ERROR: File not found: {src}", file=sys.stderr); sys.exit(1)
    try:
        data = json.loads(src.read_text())
    except json.JSONDecodeError:
        print("ERROR: Invalid JSON", file=sys.stderr); sys.exit(1)
    if "installed" not in data and "web" not in data:
        print("ERROR: Not an OAuth client-secret file", file=sys.stderr); sys.exit(1)
    CLIENT_SECRET_PATH.write_text(json.dumps(data, indent=2))
    print(f"OK: Saved to {CLIENT_SECRET_PATH}")


def get_auth_url():
    if not CLIENT_SECRET_PATH.exists():
        print("ERROR: No client secret found.", file=sys.stderr)
        print(f"Expected at: {CLIENT_SECRET_PATH}", file=sys.stderr)
        print("To get one:", file=sys.stderr)
        print("  1. Go to https://console.cloud.google.com → APIs & Services → Credentials", file=sys.stderr)
        print("  2. Create OAuth client ID (type: Desktop app)", file=sys.stderr)
        print("  3. Download the JSON file", file=sys.stderr)
        print(f"  4. Run: setup.py --client-secret /path/to/client_secret.json", file=sys.stderr)
        sys.exit(1)
    _ensure_deps()
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH), scopes=SCOPES,
        redirect_uri=REDIRECT_URI, autogenerate_code_verifier=True,
    )
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    PENDING_PATH.write_text(json.dumps({
        "state": state,
        "code_verifier": flow.code_verifier,
        "redirect_uri": REDIRECT_URI,
    }, indent=2))
    print(auth_url)


def exchange_auth_code(code_or_url: str):
    if not CLIENT_SECRET_PATH.exists():
        print("ERROR: No client secret found.", file=sys.stderr)
        print(f"Expected at: {CLIENT_SECRET_PATH}", file=sys.stderr)
        print(f"Run: setup.py --client-secret /path/to/client_secret.json", file=sys.stderr)
        sys.exit(1)
    pending = _load_pending()

    # Accept full URL or bare code
    code = code_or_url
    if code_or_url.startswith("http"):
        parsed = urllib.parse.urlparse(code_or_url)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" not in params:
            print("ERROR: No 'code' in URL", file=sys.stderr); sys.exit(1)
        code = params["code"][0]

    _ensure_deps()
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH), scopes=SCOPES,
        redirect_uri=pending.get("redirect_uri", REDIRECT_URI),
        state=pending["state"], code_verifier=pending["code_verifier"],
    )
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)

    TOKEN_PATH.write_text(flow.credentials.to_json())
    PENDING_PATH.unlink(missing_ok=True)
    print(f"OK: Token saved to {TOKEN_PATH}")


def revoke():
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
    if PENDING_PATH.exists():
        PENDING_PATH.unlink()
    print("Revoked and cleaned up local files.")


# ── main ──────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Google Docs OAuth2 setup")
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--check", action="store_true")
    grp.add_argument("--client-secret", metavar="PATH")
    grp.add_argument("--auth-url", action="store_true")
    grp.add_argument("--auth-code", metavar="CODE_OR_URL")
    grp.add_argument("--revoke", action="store_true")
    args = p.parse_args()

    if args.check:
        sys.exit(0 if check_auth() else 1)
    elif args.client_secret:
        store_client_secret(args.client_secret)
    elif args.auth_url:
        get_auth_url()
    elif args.auth_code:
        exchange_auth_code(args.auth_code)
    elif args.revoke:
        revoke()


if __name__ == "__main__":
    main()
