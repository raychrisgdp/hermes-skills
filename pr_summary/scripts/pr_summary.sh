#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# PR Summary Generator
# 
# Generates a Pull Request activity summary report for a GitHub 
# user across specified repositories within an organization.
#
# Usage:
#   ./pr_summary.sh -u <username> -o <org> [OPTIONS]
#
# Options:
#   -u USER       GitHub username (required)
#   -o ORG        GitHub organization (default: GDP-ADMIN)
#   -d DAYS       Number of days to look back (default: 7)
#   -f FILENAME   Output filename (default: pr_activity_report.md)
#   -l LIST       Comma-separated list of repos (default: all org)
#   -h            Show this help message
#
# Examples:
#   ./pr_summary.sh -u raychrisgdp -o GDP-ADMIN -d 7
#   ./pr_summary.sh -u johndoe -d 14 -f weekly_report.md
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Defaults ──────────────────────────────────────────────────
GITHUB_USER=""
GITHUB_ORG="GDP-ADMIN"
LOOKBACK_DAYS=7
OUTPUT_FILE="pr_activity_report.md"
REPO_LIST=""

# ─── Setup and Parsing ─────────────────────────────────────────
print_usage() {
    echo "═══════════════════════════════════════════════════════════════"
    echo " PR Summary Generator"
    echo "═══════════════════════════════════════════════════════════════"
    echo "Generates a Pull Request activity summary report." 
    echo ""
    echo "Usage: $0 -u <username> [OPTIONS]"
    echo ""
    echo "Required:"
    echo "  -u USER    GitHub username"
    echo ""
    echo "Options (Defaults):"
    echo "  -o ORG     Organization (default: GDP-ADMIN)"
    echo "  -d DAYS    Days to look back (default: 7)"
    echo "  -f FILE    Output file (default: pr_activity_report.md)"
    echo "  -l LIST    Specific repos, comma-separated (default: all)"
    exit 0
}

while getopts "u:o:d:f:l:h" opt; do
    case $opt in
        u) GITHUB_USER="$OPTARG" ;;
        o) GITHUB_ORG="$OPTARG" ;;
        d) LOOKBACK_DAYS="$OPTARG" ;;
        f) OUTPUT_FILE="$OPTARG" ;;
        l) REPO_LIST="$OPTARG" ;;
        h) print_usage ;;
        *) print_usage ;;
    esac
done

if [ -z "$GITHUB_USER" ]; then
    echo "❌ Error: GitHub username (-u) is required"
    print_usage
fi

# ─── Dependency Checks ─────────────────────────────────────────
echo "🔍 Checking dependencies..."
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed. Install it at https://cli.github.com"
    echo "   Run: gh auth login"
    exit 1
fi

if ! gh auth status &> /dev/null 2>&1; then
    echo "❌ Not authenticated with GitHub. Run: gh auth login"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required."
    exit 1
fi
echo "✅ Setup OK."

# ─── Date Calculation ──────────────────────────────────────────
# Compatible with GNU and BSD date
CUTOFF_DATE=$(date -d "$LOOKBACK_DAYS days ago" +%Y-%m-%d 2>/dev/null || date -v"-${LOOKBACK_DAYS}d" +%Y-%m-%d 2>/dev/null)
echo "📅 Period: Last $LOOKBACK_DAYS days (since $CUTOFF_DATE)"

# ─── Repo Filter ───────────────────────────────────────────────
REPO_FILTER="org:${GITHUB_ORG}"
if [ -n "$REPO_LIST" ]; then
    IFS=',' read -ra REPOS <<< "$REPO_LIST"
    OR_CONDITIONS=""
    for repo in "${REPOS[@]}"; do
        repo="${repo## }"
        repo="${repo%% }"
        if [ -z "$OR_CONDITIONS" ]; then
            OR_CONDITIONS="repo:${GITHUB_ORG}/${repo}"
        else
            OR_CONDITIONS="${OR_CONDITIONS} OR repo:${GITHUB_ORG}/${repo}"
        fi
    done
    REPO_FILTER="($OR_CONDITIONS)"
fi

# ─── GraphQL Query Helper ──────────────────────────────────────
query_prs() {
    local query_string="$1"
    
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
              author { login }
            }
          }
        }
      }
    }' --field q="$query_string" 2>/dev/null || echo '{"data":{"search":{"edges":[]}}}'
}

# ─── Run Queries ───────────────────────────────────────────────
echo "📥 Fetching activity data..."

AUTHORED_JSON=$(query_prs "${REPO_FILTER} author:${GITHUB_USER} is:pr created:>=${CUTOFF_DATE}")
REVIEWED_JSON=$(query_prs "${REPO_FILTER} reviewed-by:${GITHUB_USER} is:pr updated:>=${CUTOFF_DATE}")
COMMENTED_JSON=$(query_prs "${REPO_FILTER} commenter:${GITHUB_USER} is:pr updated:>=${CUTOFF_DATE}")

# ─── Generate Report ──────────────────────────────────────────
export GITHUB_USER GITHUB_ORG LOOKBACK_DAYS CUTOFF_DATE OUTPUT_FILE
export AUTHORED_JSON REVIEWED_JSON COMMENTED_JSON

echo "✨ Generating report..."

python3 << 'PYTHON_SCRIPT'
import json, os, subprocess, sys
from datetime import datetime

user = os.environ.get("GITHUB_USER")
org = os.environ.get("GITHUB_ORG")
cutoff = os.environ.get("CUTOFF_DATE")
days = os.environ.get("LOOKBACK_DAYS")
output_file = os.environ.get("OUTPUT_FILE")

# Parse Inputs
authored = json.loads(os.environ.get("AUTHORED_JSON", "{}")).get("data", {}).get("search", {}).get("edges", [])
reviewed = json.loads(os.environ.get("REVIEWED_JSON", "{}")).get("data", {}).get("search", {}).get("edges", [])
commented = json.loads(os.environ.get("COMMENTED_JSON", "{}")).get("data", {}).get("search", {}).get("edges", [])

prs = {}

def process_edges(edges, role):
    for edge in edges:
        node = edge.get("node", {})
        if not node: continue
        url = node.get("url", "")
        if not url or "Close:" in node.get("title", ""): continue
        
        title = node.get("title", "")
        repo = node.get("repository", {}).get("nameWithOwner", "unknown")
        is_merged = node.get("mergedAt") is not None
        state = node.get("state", "OPEN")
        
        # Determine status marker
        if is_merged:
            marker = "✅"
            status_str = "Merged"
        elif state == "OPEN":
            marker = "🟡 WIP"
            status_str = "Open"
        else:
            marker = "🔴"
            status_str = state
            
        # Add to collection
        if url not in prs:
            prs[url] = {
                "title": title,
                "url": url,
                "repo": repo,
                "role": role,
                "status": status_str,
                "updated": node.get("updatedAt") or node.get("createdAt", ""),
                "number": node.get("number")
            }

process_edges(authored, "Implement")
process_edges(reviewed, "Review")
process_edges(commented, "Review")

# Check commits for "Review & Implement"
# A reviewed PR counts as "Review & Implement" if the user appears as a commit
# author, co-author, or committer on that PR's branches.
print("🔍 Checking for commit authorship (Review & Implement)...")
for url, pr in list(prs.items()):
    if pr.get("role") == "Review":
        parts = url.split("/pull/")
        if len(parts) < 2: continue
        num = parts[1]
        repo = pr.get("repo")

        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/pulls/{num}/commits"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                commits = json.loads(result.stdout)
                for commit in commits:
                    commit_data = commit.get("commit", {})

                    # Check author name and email
                    author_name = commit_data.get("author", {}).get("name", "")
                    author_email = commit_data.get("author", {}).get("email", "")
                    committer_email = commit_data.get("committer", {}).get("email", "")

                    # Also check GitHub-level author (more reliable for web commits)
                    github_author = commit.get("author", {}).get("login", "")

                    msg = commit_data.get("message", "")

                    # Match on GitHub login, commit author name/email, or Co-authored-by
                    is_github_author = github_author == user
                    is_named_in_commit = user in author_name if author_name else False

                    has_author_email = "@" in (author_email or "")
                    if has_author_email:
                        email_prefix = author_email.split("@")[0]
                    else:
                        email_prefix = ""

                    is_author_by_email = author_email == user if author_email else False
                    is_prefix_match = (email_prefix and author_email and email_prefix == author_email.split("@")[0]) if has_author_email else False

                    co_authored = "Co-authored-by:" in msg
                    co_authored_matches = co_authored and (user in msg or author_email in msg or email_prefix in msg)

                    if (is_github_author or is_named_in_commit or is_author_by_email or is_prefix_match or co_authored_matches):
                        prs[url]["role"] = "Review & Implement"
                        print(f"  → Found contribution in: {pr['title']}")
                        break
        except Exception:
            pass

# Sort by date (most recent first)
def parse_date(d):
    try: return datetime.fromisoformat(d.replace("Z", "+00:00"))
    except: return datetime(2000, 1, 1)

sorted_prs = sorted(prs.values(), key=lambda x: parse_date(x.get("updated", "")), reverse=True)

# Generate Markdown
md = []
md.append(f"# PR Summary Report")
md.append(f"**User:** [{user}](https://github.com/{user}) | **Org:** {org}")
md.append(f"**Period:** {days} days (since {cutoff})")
md.append("\n---\n")

# Stats counters
stats = {"Implement": 0, "Review": 0, "Review & Implement": 0, "Open": 0}

for i, pr in enumerate(sorted_prs, 1):
    role = pr.get("role")
    if role in stats: stats[role] += 1
    if "WIP" in pr.get("status", ""): stats["Open"] += 1
    if "Open" in pr.get("status", "") and "WIP" not in pr.get("status", ""): stats["Open"] += 1
    
    title = pr.get("title")
    repo = pr.get("repo")
    num = pr.get("number", "")
    status = pr.get("status")
    # Check if merged specifically
    is_merged = "Merged" in status
    
    line = f"{i}. **{role}**: [{title}]({pr['url']}) `#{num}` — _{repo}_ ({status})"
    md.append(line)

md.append("\n---\n")
md.append("### Summary Statistics")
md.append(f"| Category | Count |")
md.append(f"|---|---|")
md.append(f"| **Implement** | {stats['Implement']} |")
md.append(f"| **Review** | {stats['Review']} |")
md.append(f"| **Review & Implement** | {stats['Review & Implement']} |")
md.append(f"| **Open / WIP** | {stats['Open']} |")
md.append(f"| **Total** | {len(sorted_prs)} |")

# Write output
output_text = "\n".join(md)
with open(output_file, "w") as f:
    f.write(output_text)

print(output_text)
print(f"\n💾 Saved to {output_file}")
PYTHON_SCRIPT