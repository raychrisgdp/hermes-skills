# Auth and Setup

## Overview

The google-docs skill uses OAuth2 to access your Google account.
You need two things:

1. **A Google Cloud project** with Docs API and Drive API enabled, plus an OAuth client ID.
2. **A token** obtained by running the auth flow on your machine.

If you already have both, just run the check:

```
python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --check
```

If it prints `AUTHENTICATED` or `AUTHENTICATED (refreshed)`, you are done.
If not, follow the steps below.

---

## Step 1 — Create a Google Cloud project (one-time)

Skip this if you already have a project with Docs and Drive APIs enabled.

1. Go to **https://console.cloud.google.com**
2. Click the project dropdown (top bar) → **New Project**
3. Name it anything (e.g. `hermes-gdocs`) → **Create**
4. Make sure the new project is selected in the dropdown

## Step 2 — Enable the APIs

1. In Cloud Console, go to **APIs & Services → Library**
2. Search **Google Docs API** → click it → **Enable**
3. Search **Google Drive API** → click it → **Enable**

## Step 3 — Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**
2. Choose **External** (unless you are in a Workspace org, then Internal is fine) → **Create**
3. Fill in:
   - App name: anything (e.g. `Hermes Docs`)
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. On the **Scopes** step, click **Add or Remove Scopes** and add:
   - `https://www.googleapis.com/auth/documents`
   - `https://www.googleapis.com/auth/drive`
6. **Save and Continue** through the rest (skip test users for now)
7. On the summary page, note the warning about verification — for personal use you can ignore it

## Step 4 — Create OAuth client credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name: anything (e.g. `hermes-desktop`)
5. Click **Create**
6. A dialog shows the client ID and secret. Click **Download JSON**
7. Save the file somewhere safe (e.g. `~/Downloads/client_secret_....json`)

The downloaded file looks like this:

```json
{
  "installed": {
    "client_id": "123456789-xxxxx.apps.googleusercontent.com",
    "client_secret": "GOCSPX-xxxxx",
    "redirect_uris": ["http://localhost"]
  }
}
```

## Step 5 — Store the client secret

```
python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --client-secret ~/Downloads/client_secret_XXXXX.json
```

This copies the file to `~/.hermes/google_client_secret.json`.

## Step 6 — Run the auth flow

**6a. Get the auth URL:**

```
python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --auth-url
```

It prints a long URL. Copy it.

**6b. Visit the URL in your browser:**

- Sign in with the Google account you want to use for docs
- Grant the permissions (Docs + Drive access)
- After approving, the browser redirects to `http://localhost/?code=4/0AX4Xf...`

**6c. Copy the full redirect URL and exchange it for a token:**

```
python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --auth-code "http://localhost/?code=4/0AX4XfWhATEVER"
```

Or just paste the bare code:

```
python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --auth-code "4/0AX4XfWhATEVER"
```

It saves the token to `~/.hermes/google_token.json`.

## Step 7 — Verify

```
python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --check
```

Should print `AUTHENTICATED`.

---

## Files involved

| File | What | Created by |
|------|------|-----------|
| `~/.hermes/google_client_secret.json` | OAuth client ID + secret | You (step 4) then `setup.py --client-secret` (step 5) |
| `~/.hermes/google_oauth_pending.json` | Temporary state for auth flow | `setup.py --auth-url` (step 6a) |
| `~/.hermes/google_token.json` | Access + refresh token | `setup.py --auth-code` (step 6c) |

`google_oauth_pending.json` is deleted after a successful auth.
`google_token.json` auto-refreshes when the access token expires.

## Scopes

| Scope | What it grants |
|-------|---------------|
| `https://www.googleapis.com/auth/documents` | Read/write all Google Docs |
| `https://www.googleapis.com/auth/drive` | Read/write all Drive files (needed for import, search, image upload) |

## Troubleshooting

**`setup.py --check` says `NOT_AUTHENTICATED`**
You have not run the auth flow yet. Go to step 6.

**`setup.py --check` says `REFRESH_FAILED`**
Your token is expired and can't be refreshed. Revoke and re-auth:
```
python3 setup.py --revoke
```
Then repeat steps 6-7.

**Browser says "This app isn't verified"**
For personal use, click **Advanced → Go to Hermes Docs (unsafe)** to bypass.
This only matters for apps published to the public — personal use is fine.

**Browser redirects to localhost but nothing happens**
The redirect goes to `http://localhost:1` which doesn't serve a page.
That's expected. Copy the full URL from the address bar and use it with `--auth-code`.

**`client_secret` format error**
Make sure you downloaded the JSON as **Desktop app** type, not Web application.
The file must have an `"installed"` key at the top level.

## Revoking access

```
python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --revoke
```

This deletes local files. To fully revoke from Google's side, go to
**https://myaccount.google.com/permissions** and remove the app.

## When to mention this to the user

- Only when auth is the blocker (setup.py --check fails).
- Otherwise, keep it implicit and continue with the doc task.
