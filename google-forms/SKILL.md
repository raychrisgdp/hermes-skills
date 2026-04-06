---
name: google-forms
description: Create and manage Google Forms via Google Apps Script Web App.
tags: ["Google", "Forms", "Automation"]
---

# Google Forms Skill

Create and manage Google Forms from the CLI using a Google Apps Script Web App.

## Active Local Configuration
The web-app URL and shared secret for the currently configured user.
**DO NOT ASK USER TO REDEPLOY UNLESS NECESSARY.**

- `WEB_APP_URL`: (empty — set after deployment)
- `WEB_APP_SECRET`: (empty — run `scripts/generate_secret.sh` and paste the output)

Example curl request when configured:
```
curl -s -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{"secret": "'"$WEB_APP_SECRET"'", "action": "list"}'
```

## For Other Users (Setup Guide)
*To create forms on a new account, you must deploy the script:*
1. **Open**: [script.new](https://script.new)
2. **Generate Secret**: Run `bash scripts/generate_secret.sh` locally, copy the `SHARED_SECRET = '...'` line.
3. **Paste Code**: Copy `scripts/appscript_code.gs` and paste it. Set `SHARED_SECRET` to the generated value at the top of the script.
4. **Deploy**: New deployment -> Web app -> Execute as: Me -> Access: Anyone.
5. **Share URL**: Copy the generated URL and set `WEB_APP_URL` in this SKILL.md.

## Agent Instructions
1. **Check for Active URL and Secret**: Both `WEB_APP_URL` and `WEB_APP_SECRET` must be set.
2. **If both are set**: Use them immediately for curl commands, including `"secret"` in the JSON body.
3. **If either is missing**: Guide the user through the Setup Guide above.

## Architecture & Scripts
* **CLI Wrapper**: `scripts/forms_api.py` (Handles OAuth if not using Web App).
* **Web App Script**: `scripts/appscript_code.gs` (authenticates via shared secret).
* **Secret Generator**: `scripts/generate_secret.sh` (produces a random secret).
