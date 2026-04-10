---
name: google-forms
description: Create and manage Google Forms via Google Apps Script Web App.
tags: ["Google", "Forms", "Automation"]
---

# Google Forms Skill

Create and manage Google Forms from the CLI using a Google Apps Script Web App.

## Active Local Configuration
This skill does not use a traditional `.env` file.
The runtime config lives in `~/.hermes/google_forms_config` and contains two lines:
- `WEB_APP_URL=https://script.google.com/macros/s/.../exec`
- `WEB_APP_SECRET=...`

**Do not ask the user to redeploy unless necessary.**

Read the config at runtime:
```bash
WEB_APP_URL=$(sed -n '1s/^WEB_APP_URL=//p' ~/.hermes/google_forms_config)
WEB_APP_SECRET=$(sed -n '2s/^WEB_APP_SECRET=//p' ~/.hermes/google_forms_config)
```

Then use it in curl commands:
```bash
curl -s -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{"secret":"'"$WEB_APP_SECRET"'","action":"list"}'
```

## For Other Users (Setup Guide)
*To create forms on a new account, you must deploy the script:*
1. **Open**: [script.new](https://script.new)
2. **Generate Secret**: Run `bash scripts/generate_secret.sh` locally, copy the generated secret.
3. **Paste Code**: Copy `scripts/appscript_code.gs` and paste it. Set `SHARED_SECRET` to the generated value at the top of the script.
4. **Deploy**: New deployment -> Web app -> Execute as: Me -> Access: Anyone.
5. **Save URL**: Create `~/.hermes/google_forms_config` with both `WEB_APP_URL` and `WEB_APP_SECRET`.

## Agent Instructions
1. **Check for credential file**: `~/.hermes/google_forms_config` must exist with both `WEB_APP_URL` and `WEB_APP_SECRET` lines populated.
2. **If both are set**: Read values at runtime and use immediately, including `"secret"` in the JSON body.
3. **If the file or either value is missing**: Guide the user through the Setup Guide above.

## Architecture & Scripts
* **CLI Wrapper**: `scripts/forms_api.py` (Handles OAuth if not using Web App).
* **Web App Script**: `scripts/appscript_code.gs` (authenticates via shared secret, fails closed).
* **Secret Generator**: `scripts/generate_secret.sh` (produces a random secret).
