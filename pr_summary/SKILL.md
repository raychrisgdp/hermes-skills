---
name: pr_summary
description: "Generate a weekly PR activity summary report using GitHub API search queries. Searches org:GDP-ADMIN for a user's authored, reviewed, and commented PRs with bot filtering and role detection."
---

# PR Summary

Generates a Pull Request activity summary report for a GitHub user across specified repositories within the org.

## Context

This works in both OpenCode (`~/.opencode/command/pr-summary.md` origin) and Hermes.
All queries target `org:GDP-ADMIN` using the GitHub API via `gh` CLI or `curl` + GitHub REST API.
User identity: `raychrisgdp`.

## Workflow

### 1. Determine Cutoff Date

Default: 7 days before today. Calculate:
```bash
date -d "7 days ago" +%Y-%m-%d  # Linux
```

### 2. Query Authored PRs (GraphQL)

**Use `gh api graphql` not `gh search prs`**. The REST/CLI search returns truncated data and lacks `isMerged`. GraphQL gives full fields in one call.

```bash
gh api graphql -f query='
query($q: String!) {
  search(query: $q, type: ISSUE, first: 100) {
    edges {
      node {
        ... on PullRequest {
          number
          title
          url
          state
          createdAt
          updatedAt
          repository { nameWithOwner }
          mergedAt
        }
      }
    }
  }
}
' --field q="org:GDP-ADMIN author:raychrisgdp is:pr created:>=$CUTOFF"
```

**Important**: Use `mergedAt` to detect merged PRs (don't look for `isMerged` — it doesn't exist in the GraphQL schema; `mergedAt: null` = not merged).

### 3. Query Reviewed/Commented PRs (GraphQL)

Run **two** separate queries. The `reviewed-by:` filter only catches formal reviews, but the user often leaves non-review comments and closure comments that are equally important.

**Query A — Reviewed:**
```bash
--field q="org:GDP-ADMIN reviewed-by:raychrisgdp is:pr updated:>=$CUTOFF"
```

**Query B — Commented:**
```bash
--field q="org:GDP-ADMIN commenter:raychrisgdp is:pr updated:>=$CUTOFF"
```

Merge both result sets (deduplicate by URL).

**IMPORTANT:** EXCLUDE "Close:" entries entirely. If the user's ONLY activity on a PR is a closure comment (no code review, no review), skip it. Do not list it, do not count it, do not include it in the report. Only include:
- "Review": user left an actual code review
- "Review & Implement": user reviewed AND contributed code (check Co-authored-by below)
- "Implement": user is the PR author

### 4. Filter Bot Activity

For authored PRs created near cutoff (within 3 days), verify recent activity is from the user, not bots. Exclude comments/reviews from:
- `github-actions[bot]`
- `sonarqubecloud[bot]`
- `sca-gdplabs[bot]`
- Any user with `[bot]` suffix

### 5. Detect Roles

- **Implement**: User is the PR author
- **Review**: User reviewed/commented but did not author
- **Review & Implement**: User is not author but contributed code (`Co-authored-by: Raymond Christopher` in commit messages, or commits with author login `raychrisgdp`)

Add `(WIP)` for open PRs.

### 6. Sort & Format

Sort all PRs globally by user's last activity date descending (most recent first). Do NOT group by repo — single continuous numbered list.

```
# PR Summary (since YYYY-MM-DD)

Cutoff date: YYYY-MM-DD

1. Role[(WIP)]: PR title [#number](link)
2. Role: PR title [#number](link)
...
```

### 7. Save & Report

- Save to `pr_activity_report.md` (or `{filename}_summary.md` if filename specified)
- Display breakdown:
  - Total PRs count
  - By repository
  - By role (Implement vs Review vs Review & Implement)
  - WIP (open) PRs list

## Constraints

- **CRITICAL**: For authored PRs, always use `created:>=<date>`, NOT `updated:>=<date>`. The `updated:` filter includes activity from ANY user (bots, reviewers, SonarCloud) causing false positives.
- For reviewed/commented PRs, `reviewed-by:` and `commenter:` filters are accurate for user activity.
- Exclude PRs where only bots were active recently.
- Deduplicate PRs appearing in multiple search results.
- Check commit history for `Co-authored-by` to detect "Review & Implement" cases.
- **GraphQL note**: `isMerged` doesn't exist on PullRequest type. Use `mergedAt` (null = open/closed, non-null = merged).
- **Auth requirement**: Must be authenticated via `gh auth login` on the machine.
- **"Close:" role**: EXCLUDED. The user does not want closure-only activity in reports. Skip PRs where the user's only interaction was closing the PR.
- **Comparison baseline**: The original OpenCode command at `~/.opencode/command/pr-summary.md` includes ~17 Close-only entries. The expected output WITHOUT Close entries is ~45-48 PRs for a 7-day window.

## Origin

The canonical definition lives at `~/.opencode/command/pr-summary.md` as an OpenCode custom slash command (`/pr-summary`).
This skill adapts that command's logic for execution outside the OpenCode TUI (Hermes sessions, cron jobs, shell scripts).
