# Auth and Setup

## What to do first
- Run `python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --check`.
- If it prints `AUTHENTICATED` or `AUTHENTICATED (refreshed)`, proceed.
- If not, refresh credentials before touching docs.

## Credential facts
- Normal access uses the token at `~/.hermes/google_token.json`.
- The token auto-refreshes when possible.
- The skill uses user OAuth, not a service account, for personal docs.

## Common failure mode
- If auth fails, do not guess around it.
- Re-run setup and confirm the check passes before publishing.

## When to mention this to the user
- Only when auth is the blocker.
- Otherwise, keep it implicit and continue with the doc task.
