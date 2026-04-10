#!/usr/bin/env python3
"""Google Forms web-app helper — no curl pipes, no shell tricks.

Usage:
    python3 gform.py '{"action":"list"}'
    python3 gform.py create --title "My Form" --questions questions.json
    python3 gform.py get FORM_ID
    python3 gform.py list
    python3 gform.py responses FORM_ID

Env:
    GFORMS  — Web App URL (required)

The web app always returns a 302 redirect. This script follows it automatically.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

_ENV_PATH = Path.home() / "gform_automation" / ".env"


def load_env() -> dict[str, str]:
    """Load GFORMS from ~/gform_automation/.env if not already in os.environ."""
    env = {}
    if _ENV_PATH.exists():
        for line in _ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def get_url() -> str:
    url = os.environ.get("GFORMS")
    if not url:
        env = load_env()
        url = env.get("GFORMS")
    if not url:
        print("ERROR: GFORMS not set. Create ~/gform_automation/.env or export GFORMS.", file=sys.stderr)
        sys.exit(1)
    return url


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Suppress automatic redirect following."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def post_and_follow(payload: dict) -> str:
    """POST JSON to the web app, follow redirect as GET, return response body.

    Google Apps Script returns 302 to script.googleusercontent.com.
    urllib's default redirect re-POSTs which hangs. We manually follow as GET.
    """
    url = get_url()
    data = json.dumps(payload).encode()

    # Step 1: POST — expect 302 with Location header
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        _opener.open(req, timeout=15)
    except urllib.error.HTTPError as e:
        if e.code == 302:
            location = e.headers.get("Location")
            if location:
                # Step 2: GET the redirect URL
                get_req = urllib.request.Request(location, method="GET")
                resp = urllib.request.urlopen(get_req, timeout=30)
                return resp.read().decode()
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    return ""


def cmd_list():
    return post_and_follow({"action": "list"})


def cmd_get(form_id: str):
    return post_and_follow({"action": "get", "formId": form_id})


def cmd_responses(form_id: str):
    return post_and_follow({"action": "responses", "formId": form_id})


def cmd_create(title: str, description: str = "", questions: list | None = None):
    payload = {"action": "create", "title": title}
    if description:
        payload["description"] = description
    if questions:
        payload["questions"] = questions
    return post_and_follow(payload)


def cmd_add_questions(form_id: str, questions: list):
    return post_and_follow({"action": "addQuestions", "formId": form_id, "questions": questions})


def main():
    if len(sys.argv) < 2:
        print("Usage: gform.py <json-payload | command> [args...]", file=sys.stderr)
        print("  gform.py '{\"action\":\"list\"}'", file=sys.stderr)
        print("  gform.py list", file=sys.stderr)
        print("  gform.py get FORM_ID", file=sys.stderr)
        print("  gform.py responses FORM_ID", file=sys.stderr)
        print("  gform.py create --title 'My Form' [--questions questions.json]", file=sys.stderr)
        print("  gform.py add-questions FORM_ID questions.json", file=sys.stderr)
        sys.exit(1)

    arg1 = sys.argv[1]

    # Raw JSON mode: gform.py '{"action":"list"}'
    if arg1.startswith("{"):
        payload = json.loads(arg1)
        print(post_and_follow(payload))
        return

    # Command mode
    cmd = arg1.lower()

    if cmd == "list":
        print(cmd_list())

    elif cmd == "get":
        if len(sys.argv) < 3:
            print("Usage: gform.py get FORM_ID", file=sys.stderr)
            sys.exit(1)
        print(cmd_get(sys.argv[2]))

    elif cmd == "responses":
        if len(sys.argv) < 3:
            print("Usage: gform.py responses FORM_ID", file=sys.stderr)
            sys.exit(1)
        print(cmd_responses(sys.argv[2]))

    elif cmd == "create":
        title = ""
        description = ""
        questions = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--title" and i + 1 < len(sys.argv):
                title = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--description" and i + 1 < len(sys.argv):
                description = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--questions" and i + 1 < len(sys.argv):
                qfile = Path(sys.argv[i + 1])
                questions = json.loads(qfile.read_text()); i += 2
            else:
                i += 1
        if not title:
            print("Usage: gform.py create --title 'My Form' [--questions questions.json]", file=sys.stderr)
            sys.exit(1)
        print(cmd_create(title, description, questions))

    elif cmd == "add-questions":
        if len(sys.argv) < 4:
            print("Usage: gform.py add-questions FORM_ID questions.json", file=sys.stderr)
            sys.exit(1)
        form_id = sys.argv[2]
        qfile = Path(sys.argv[3])
        questions = json.loads(qfile.read_text())
        print(cmd_add_questions(form_id, questions))

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
