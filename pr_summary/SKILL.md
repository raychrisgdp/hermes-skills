---
name: pr_summary
description: Generate a PR activity summary using a self-contained script.
tags: ["GitHub", "PR", "Workflow", "Automation"]
---

# PR Summary Skill

Generates a comprehensive Pull Request activity summary.

## ✍️ What can I do for you?

*   "What's my weekly PR summary?"
*   "Generate a report for @johndoe for the last 14 days."
*   "Save my activity for the 'frontend' repo to a file called `frontend_report.md`."

## 🤖 Agent Interaction Guide (How I handle requests)

### 1. Check for Parameters
Before running, I ask myself: "Do I have the username?"
*   **No username?** I will ask: "Who should I generate the report for?"
*   **No timeframe?** I will ask: "Should I look at the last 7 days?" (or use 7 as default).

### 2. Validate Script
I ensure `scripts/pr_summary.sh` exists.
*   **If missing?** "I can't find the PR summary script locally."
*   **If present?** Proceed to run it.

### 3. Execution
I run the script with your parameters:
`./scripts/pr_summary.sh -u <username> -d <days>`

## ⚙️ Setup (One-Time)
You need the GitHub CLI installed and logged in:
1. `sudo apt install gh` (or download from cli.github.com)
2. `gh auth login`
