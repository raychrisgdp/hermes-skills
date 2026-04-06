#!/bin/bash
set -euo pipefail
# Generate a random shared secret for Google Forms web-app authentication.
# Run this once, then copy the output into your SKILL.md and appscript_code.gs.
# The secret must match in both places.

SECRET=$(openssl rand -hex 32)
echo "=== Your shared secret ==="
echo "$SECRET"
echo ""
echo "Add this line to the top of scripts/appscript_code.gs:"
echo "  var SHARED_SECRET = '$SECRET';"
echo ""
echo "And update the WEB_APP_SECRET line in your SKILL.md Active Local Configuration section."
