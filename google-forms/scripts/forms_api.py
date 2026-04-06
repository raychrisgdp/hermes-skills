#!/usr/bin/env python3
"""Google Forms API CLI wrapper.

Usage:
    forms_api.py create --title "My Form" [--description "..."] [--question JSON]...
    forms_api.py list
    forms_api.py get FORM_ID
    forms_api.py update FORM_ID [--title "..."] [--description "..."]
    forms_api.py add-question FORM_ID --question JSON [--question JSON]...
    forms_api.py delete-question FORM_ID QUESTION_ID
    forms_api.py settings FORM_ID [--collect-email BOOL] [--limit-response BOOL] [--confirmation-message "..."]
    forms_api.py responses FORM_ID [RESPONSE_ID]
    forms_api.py link-sheet FORM_ID [--sheet-id SHEET_ID]

Question JSON schema (see SKILL.md for full table):
    Required: type, title
    Types: text, paragraph, multiple_choice, checkbox, dropdown, scale,
           linear_scale, date, time, email, phone
    Type-specific: options (for choice types), required (bool),
                   scaleMin/scaleMax (for scale), shuffle (bool), min/max (checkbox)
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ── Self-contained Google OAuth helpers ─────────────────────────────
# These avoid the fragile cross-skill import to productivity/google-workspace.

SCOPES = [
    "https://www.googleapis.com/auth/forms",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

TOKEN_DIR = Path.home() / ".hermes" / "google_tokens"
TOKEN_FILE = TOKEN_DIR / "forms_token.json"


def get_credentials():
    """Load Google API credentials from a local token file.

    If no valid credentials exist, raise a clear error telling the user
    what to do.  The caller should catch this and print actionable guidance.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"No token found at {TOKEN_FILE}.\n"
            "Run 'python3 scripts/setup.py' in the google-forms skill directory first."
        )

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())

    if not creds or not creds.valid:
        raise ValueError(
            f"Token at {TOKEN_FILE} is invalid or missing refresh token.\n"
            "Re-run the setup to re-authenticate."
        )
    return creds


def handle_api_error(error):
    """Pretty-print an HttpError from the Google API client."""
    from googleapiclient.errors import HttpError
    if isinstance(error, HttpError):
        status = error.resp.status
        body = error._get_reason() or str(error)
        print(f"API error {status}: {body}", file=sys.stderr)
    else:
        print(f"Error: {error}", file=sys.stderr)


def build_services():
    from googleapiclient.discovery import build
    creds = get_credentials()
    forms = build("forms", "v1", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return forms, sheets, drive


# ── create ───────────────────────────────────────────────────────────────────
def create_form(args):
    forms_s, _, _ = build_services()
    body = {
        "info": {
            "title": args.title,
        }
    }
    if args.description:
        body["info"]["description"] = args.description

    # Collect question creation requests
    requests = []
    for q_json in (args.question or []):
        q = json.loads(q_json)
        req = build_question_request(q)
        requests.append(req)

    result = forms_s.forms().create(body=body).execute()
    form_id = result["formId"]

    if requests:
        batch_body = {"requests": requests}
        forms_s.forms().batchUpdate(formId=form_id, body=batch_body).execute()

    result = get_form_metadata(forms_s, form_id)
    print(json.dumps(result, indent=2))


def build_question_request(q):
    """Build a createItem request from a JSON question spec."""
    qtype = q["type"]
    title = q["title"]
    required = q.get("required", False)

    question = {"title": title, "required": required}

    if qtype == "text":
        question["textQuestion"] = {"paragraph": False}
    elif qtype == "paragraph":
        question["textQuestion"] = {"paragraph": True}
    elif qtype in ("multiple_choice", "checkbox", "dropdown"):
        options = [{"value": o} for o in q["options"]]
        if qtype == "multiple_choice":
            question["choiceQuestion"] = {
                "type": "RADIO",
                "options": options,
                "shuffle": q.get("shuffle", False),
            }
        elif qtype == "checkbox":
            question["choiceQuestion"] = {
                "type": "CHECKBOX",
                "options": options,
            }
        elif qtype == "dropdown":
            question["choiceQuestion"] = {
                "type": "DROP_DOWN",
                "options": options,
            }
    elif qtype in ("scale", "linear_scale"):
        question["scaleQuestion"] = {
            "low": q.get("scaleMin", 1),
            "high": q.get("scaleMax", 5),
        }
        if "labels" in q:
            question["scaleQuestion"]["labels"] = q["labels"]
    elif qtype == "date":
        question["dateQuestion"] = {"includeTime": False, "includeYear": True}
    elif qtype == "time":
        question["timeQuestion"] = {"duration": False}
    elif qtype == "email":
        question["textQuestion"] = {"paragraph": False}
        # Email validation is done via validator
        question["textQuestion"]["validation"] = {
            "stringValidation": {"strictMode": True}
        }
    elif qtype == "phone":
        question["textQuestion"] = {"paragraph": False}
        question["textQuestion"]["validation"] = {
            "stringValidation": {"strictMode": False}
        }
    else:
        raise ValueError(f"Unknown question type: {qtype}")

    return {"createItem": {"item": {"questionItem": {"question": question}}, "location": {"index": 0}}}


def get_form_metadata(forms_s, form_id):
    """Fetch full form details."""
    from googleapiclient.errors import HttpError
    try:
        form = forms_s.forms().get(formId=form_id).execute()

        # Try to get responses too
        try:
            resp = forms_s.forms().responses().list(formId=form_id).execute()
            form["responseCount"] = len(resp.get("responses", []))
        except HttpError:
            form["responseCount"] = "(no responses.readonly scope)"

        # Get responder and edit URIs
        info = form.get("info", {})
        form["responderUri"] = info.get("responderUri", "")
        form["editFormUri"] = info.get("editFormUri", "")

        return form
    except HttpError as e:
        handle_api_error(e)
        sys.exit(1)


# ── list ─────────────────────────────────────────────────────────────────────
def list_forms(args):
    """Forms API doesn't have a list endpoint. We use Drive API to find forms."""
    _, _, drive_s = build_services()
    results = drive_s.files().list(
        q="mimeType='application/vnd.google-apps.form'",
        fields="files(id, name, modifiedTime, webViewLink, owners)",
        orderBy="modifiedTime desc",
        pageSize=args.max if hasattr(args, "max") else 20,
    ).execute()

    files = results.get("files", [])
    if not files:
        print("No forms found.")
        return

    output = []
    for f in files:
        output.append({
            "formId": f["id"],
            "title": f["name"],
            "modifiedTime": f.get("modifiedTime"),
            "webViewLink": f.get("webViewLink"),
            "owner": f.get("owners", [{}])[0].get("displayName", "Unknown"),
        })

    print(json.dumps(output, indent=2))


# ── get ──────────────────────────────────────────────────────────────────────
def get_form(args):
    forms_s, _, _ = build_services()
    result = get_form_metadata(forms_s, args.form_id)
    print(json.dumps(result, indent=2))


# ── update ───────────────────────────────────────────────────────────────────
def update_form(args):
    forms_s, _, _ = build_services()
    requests = []

    if args.title:
        requests.append({
            "updateInfo": {
                "info": {"title": args.title},
                "updateMask": "title",
            }
        })
    if args.description:
        requests.append({
            "updateInfo": {
                "info": {"description": args.description},
                "updateMask": "description",
            }
        })

    if not requests:
        print("Nothing to update. Provide --title and/or --description.")
        return

    body = {"requests": requests}
    result = forms_s.forms().batchUpdate(formId=args.form_id, body=body).execute()
    print(json.dumps({"status": "updated", "formId": args.form_id, "result": result}, indent=2))


# ── add-question ─────────────────────────────────────────────────────────────
def add_question(args):
    forms_s, _, _ = build_services()
    requests = []
    for q_json in args.question:
        q = json.loads(q_json)
        req = build_question_request(q)
        requests.append(req)

    body = {"requests": requests}
    result = forms_s.forms().batchUpdate(formId=args.form_id, body=body).execute()
    print(json.dumps({"status": "questions_added", "formId": args.form_id, "result": result}, indent=2))


# ── delete-question ──────────────────────────────────────────────────────────
def delete_question(args):
    forms_s, _, _ = build_services()
    body = {"requests": [{"deleteItem": {"location": {"itemId": args.question_id}}}]}
    result = forms_s.forms().batchUpdate(formId=args.form_id, body=body).execute()
    print(json.dumps({"status": "deleted", "formId": args.form_id, "questionId": args.question_id}, indent=2))


# ── settings ─────────────────────────────────────────────────────────────────
def update_settings(args):
    forms_s, _, _ = build_services()
    requests = []

    if args.collect_email is not None:
        val = args.collect_email.lower() in ("true", "1", "yes")
        requests.append({
            "updateFormInfo": {
                "formInfo": {
                    "collectorEmail": val,
                },
                "updateMask": "collectorEmail",
            }
        })

    if args.limit_response is not None:
        val = args.limit_response.lower() in ("true", "1", "yes")
        requests.append({
            "updateSettings": {
                "settings": {
                    "quizSettings": {
                        "isQuiz": val,
                    }
                },
                "updateMask": "quizSettings",
            }
        })

    if args.confirmation_message:
        requests.append({
            "updateSettings": {
                "settings": {
                    "confirmationMessage": {"message": args.confirmation_message},
                },
                "updateMask": "confirmationMessage",
            }
        })

    if not requests:
        print("No settings to update. Use --collect-email, --limit-response, or --confirmation-message.")
        return

    body = {"requests": requests}
    # Some settings may need individual update calls
    for req in requests:
        try:
            forms_s.forms().batchUpdate(formId=args.form_id, body={"requests": [req]}).execute()
        except Exception as e:
            print(f"Warning: setting update failed: {e}")

    print(json.dumps({"status": "settings_updated", "formId": args.form_id}, indent=2))


# ── responses ────────────────────────────────────────────────────────────────
def list_responses(args):
    forms_s, _, _ = build_services()
    if args.response_id:
        result = forms_s.forms().responses().get(
            formId=args.form_id, responseId=args.response_id
        ).execute()
        print(json.dumps(result, indent=2))
    else:
        result = forms_s.forms().responses().list(
            formId=args.form_id
        ).execute()
        responses = result.get("responses", [])
        print(json.dumps({"formId": args.form_id, "count": len(responses), "responses": responses}, indent=2))


# ── link-sheet ───────────────────────────────────────────────────────────────
def link_to_sheet(args):
    forms_s, sheets_s, _ = build_services()

    if args.sheet_id:
        # Link to existing sheet
        body = {
            "spreadsheetId": args.sheet_id,
        }
        result = forms_s.forms().responses().linkToSpreadsheet(
            formId=args.form_id, body=body
        ).execute()
    else:
        # Create a new spreadsheet and link
        create_result = sheets_s.spreadsheets().create(
            body={"properties": {"title": "Form Responses - linked"}}
        ).execute()
        sheet_id = create_result["spreadsheetId"]
        body = {"spreadsheetId": sheet_id}
        result = forms_s.forms().responses().linkToSpreadsheet(
            formId=args.form_id, body=body
        ).execute()
        # Share the sheet URL
        print(json.dumps({
            "status": "linked",
            "formId": args.form_id,
            "spreadsheetId": sheet_id,
            "spreadsheetUrl": create_result.get("spreadsheetUrl"),
        }, indent=2))
        return

    print(json.dumps({"status": "linked", "formId": args.form_id, "result": result}, indent=2))


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Google Forms CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # create
    p_create = subparsers.add_parser("create", help="Create a new form")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--description")
    p_create.add_argument("--question", action="append", help="JSON question spec (can be repeated)")
    p_create.set_defaults(func=create_form)

    # list
    p_list = subparsers.add_parser("list", help="List all forms")
    p_list.add_argument("--max", type=int, default=20)
    p_list.set_defaults(func=list_forms)

    # get
    p_get = subparsers.add_parser("get", help="Get form details")
    p_get.add_argument("form_id")
    p_get.set_defaults(func=get_form)

    # update
    p_update = subparsers.add_parser("update", help="Update form info")
    p_update.add_argument("form_id")
    p_update.add_argument("--title")
    p_update.add_argument("--description")
    p_update.set_defaults(func=update_form)

    # add-question
    p_add = subparsers.add_parser("add-question", help="Add question(s) to form")
    p_add.add_argument("form_id")
    p_add.add_argument("--question", required=True, action="append", help="JSON question spec (can be repeated)")
    p_add.set_defaults(func=add_question)

    # delete-question
    p_del = subparsers.add_parser("delete-question", help="Delete a question")
    p_del.add_argument("form_id", help="The form ID")
    p_del.add_argument("question_id", help="The question/ item ID to delete")
    p_del.set_defaults(func=delete_question)

    # settings
    p_settings = subparsers.add_parser("settings", help="Update form settings")
    p_settings.add_argument("form_id")
    p_settings.add_argument("--collect-email", dest="collect_email")
    p_settings.add_argument("--limit-response", dest="limit_response")
    p_settings.add_argument("--confirmation-message", dest="confirmation_message")
    p_settings.set_defaults(func=update_settings)

    # responses
    p_resp = subparsers.add_parser("responses", help="List or get responses")
    p_resp.add_argument("form_id")
    p_resp.add_argument("response_id", nargs="?", default=None)
    p_resp.set_defaults(func=list_responses)

    # link-sheet
    p_link = subparsers.add_parser("link-sheet", help="Link form responses to a Google Sheet")
    p_link.add_argument("form_id")
    p_link.add_argument("--sheet-id", dest="sheet_id")
    p_link.set_defaults(func=link_to_sheet)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
