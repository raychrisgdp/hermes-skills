---
name: pr_summary
description: "Generate a weekly PR activity summary report using a self-contained script."
tags: ["GitHub", "PR", "Workflow", "Automation"]
---

# PR Summary Skill

Generates a comprehensive Pull Request activity summary for you with one simple command.

---

## ✨ What you can ask me:

* "Generate my PR summary for this week."
* "Make a report of my activity for user `johndoe` in the `my-org` organization."
* "Show me PRs for the last 14 days and save it to `report.md`."

---

## 🚀 Quick Start (Run from Terminal)

If you want to run the report yourself in the terminal, use this script:

📂 `~/hermes-skills/pr_summary/scripts/pr_summary.sh`

**Example Command:**
```bash
./pr_summary.sh -u your_username -o your_organization -d 7
```

**Options:**
* `-u` : Your GitHub username (Required)
* `-o` : GitHub Organization (Default: `GDP-ADMIN`)
* `-d` : Days to look back (Default: 7)
* `-f` : Output filename (Default: `pr_activity_report.md`)
* `-h` : Help menu

---

## ⚙️ Requirements (One-Time Setup)

1.  **GitHub CLI**: Install it from [cli.github.com](https://cli.github.com/).
2.  **Login**: Run `gh auth login` in your terminal once.

That's it! Once you're logged in, the script will automatically pull data and generate reports for any user in any organization.
