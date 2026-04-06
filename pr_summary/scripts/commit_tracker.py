#!/usr/bin/env python3
"""
Commit-Level Activity Tracker
─────────────────────────────
Finds PRs the user authored/reviewed/commented on, resolves commits per PR,
groups by UTC+7 date+hour, and logs in a time-table.

Based on the proven pr_summary.sh approach (GraphQL PR queries + per-PR commit fetch).

Usage:
    python3 commit_tracker.py [DAYS]          -- last N days (default: 7)
    python3 commit_tracker.py --since 2026-04-01 --until 2026-04-06
    python3 commit_tracker.py 7 DRY_RUN        -- skip commit detail fetch
    python3 commit_tracker.py 3 --no-pr-table  -- hide per-PR breakdown
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# ─── Config ──────────────────────────────────────────────────────
GITHUB_USER = "raychrisgdp"
ORG = "GDP-ADMIN"
UTC7 = timezone(timedelta(hours=7))


# ─── Helpers ─────────────────────────────────────────────────────

def run_gh(args, timeout=30):
    """Run gh command, return parsed JSON or None."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            err = result.stderr.strip()[:200]
            if "HTTP 404" not in err and "HTTP 403" not in err:
                print(f"  [warn] {err}", file=sys.stderr)
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  [err] {e}", file=sys.stderr)
        return None


def utc_to_utc7(iso_str):
    """Convert ISO timestamp to UTC+7 datetime."""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(UTC7)
    except (ValueError, TypeError):
        return None


def truncate(text, max_len=65):
    if not text:
        return ""
    line = text.strip().split("\n")[0]
    return line[:max_len - 3] + "..." if len(line) > max_len else line


def query_prs(q_string):
    """GraphQL search for PRs."""
    data = run_gh([
        "api", "graphql",
        "-f", f"query=query($q: String!){{search(query: $q, type: ISSUE, first: 100){{edges{{node{{...on PullRequest{{id number title url state createdAt updatedAt repository{{nameWithOwner}} mergedAt author{{login}}}}}}}}}}}}",
        "--field", f"q={q_string}",
    ], timeout=30)
    
    if not data:
        return []
    
    try:
        edges = data["data"]["search"]["edges"]
        return [e["node"] for e in edges if e.get("node")]
    except (KeyError, TypeError):
        return []


def get_commits_for_pr(repo, pr_number):
    """Get commits for a PR."""
    result = run_gh(
        ["api", f"repos/{repo}/pulls/{pr_number}/commits"],
        timeout=20
    )
    if result and isinstance(result, list):
        return result
    return []


def get_pr_author(repo, pr_number):
    """Get PR author login."""
    pr = run_gh(
        ["api", f"repos/{repo}/pulls/{pr_number}", "-f", "fields=number,user.login"],
        timeout=10
    )
    if pr:
        return pr.get("user", {}).get("login")
    return None


# ─── Main ────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    days = 7
    since_label = None
    until_label = None
    dry_run = False
    show_hours = True
    show_pr = True

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--since" and i + 1 < len(args):
            since_label = args[i + 1]
            i += 2
        elif a == "--until" and i + 1 < len(args):
            until_label = args[i + 1]
            i += 2
        elif a == "--no-hour-summary":
            show_hours = False
            i += 1
        elif a == "--no-pr-table":
            show_pr = False
            i += 1
        elif a == "DRY_RUN":
            dry_run = True
            i += 1
        else:
            try:
                days = int(a)
            except ValueError:
                pass
            i += 1

    now_utc7 = datetime.now(UTC7)
    if since_label:
        since_dt = datetime.strptime(since_label, "%Y-%m-%d")
    else:
        since_dt = now_utc7 - timedelta(days=days)

    if until_label:
        until_dt = datetime.strptime(until_label, "%Y-%m-%d") + timedelta(days=1)
    else:
        until_dt = now_utc7 + timedelta(days=1)

    cutoff = since_dt.strftime("%Y-%m-%d")
    since_label = cutoff
    until_label = (until_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Scanning PR activity by {GITHUB_USER} in {ORG} since {since_label}...", file=sys.stderr)

    # ── Phase 1: Find all PRs ──
    # Authored (created:>=)
    authored = query_prs(f"org:{ORG} author:{GITHUB_USER} is:pr created:>={cutoff} is:merged")
    authored_open = query_prs(f"org:{ORG} author:{GITHUB_USER} is:pr created:>={cutoff} is:open")
    authored = authored + authored_open
    
    # Reviewed
    reviewed = query_prs(f"org:{ORG} reviewed-by:{GITHUB_USER} is:pr updated:>={cutoff}")
    # Commented
    commented = query_prs(f"org:{ORG} commenter:{GITHUB_USER} is:pr updated:>={cutoff}")

    # Dedup by URL
    all_prs = {}
    for node_list, role in [(authored, "authored"), (reviewed, "reviewed"), (commented, "commented")]:
        for node in node_list:
            url = node.get("url", "")
            if not url:
                continue
            title = node.get("title", "")
            if title.startswith("Close:"):
                continue
            if url not in all_prs:
                all_prs[url] = {
                    "url": url,
                    "number": node.get("number"),
                    "title": node.get("title"),
                    "state": node.get("state"),
                    "repo": node.get("repository", {}).get("nameWithOwner", "?/?"),
                    "merged_at": node.get("mergedAt"),
                    "created_at": node.get("createdAt"),
                    "updated_at": node.get("updatedAt"),
                    "pr_author": node.get("author", {}).get("login"),
                    "roles": set(),
                    "commits": [],
                }
            all_prs[url]["roles"].add(role)

    prs = list(all_prs.values())
    print(f"Found {len(prs)} PRs.", file=sys.stderr)

    if not prs:
        print("\nNo PRs/commits in period.")
        return

    # ── Phase 2: Fetch commits per PR ──
    all_commits = []
    
    for idx, pr in enumerate(prs, 1):
        sys.stderr.write(f"  [{idx}/{len(prs)}] PR #{pr['number']} {pr['title'][:40]}: ")
        
        if dry_run:
            # Create a mock commit entry from PR data
            dt = utc_to_utc7(pr.get("updated_at") or pr.get("created_at") or "")
            all_commits.append({
                "sha": pr["url"],
                "repo": pr["repo"],
                "repo_short": pr["repo"].split("/")[-1],
                "dt": dt,
                "date": dt.strftime("%Y-%m-%d") if dt else "??",
                "hour": dt.hour if dt else -1,
                "time": dt.strftime("%H:%M") if dt else "??:??",
                "msg": truncate(pr["title"]),
                "pr": pr["number"],
                "pr_url": pr["url"],
                "pr_title": pr["title"],
                "pr_state": pr["state"],
                "is_merged": pr["merged_at"] is not None,
                "role": "Implement (author)",
                "commit_hash": None,
            })
            print("(dry run)", file=sys.stderr)
            continue

        commits = get_commits_for_pr(pr["repo"], pr["number"])
        print(f"{len(commits)} commits", file=sys.stderr)
        
        for c in commits:
            sha = c.get("sha", "")
            commit_data = c.get("commit", {})
            author_info = commit_data.get("author", {})
            committer_info = commit_data.get("committer", {})
            msg = commit_data.get("message", "")
            date_str = committer_info.get("date") or author_info.get("date", "")
            dt = utc_to_utc7(date_str)
            # GitHub-level author
            gh_author = c.get("author", {}).get("login", "")
            is_commit_author = gh_author == GITHUB_USER
            is_coauthor = False
            if not is_commit_author:
                is_coauthor = (
                    f"Co-authored-by: {GITHUB_USER}" in msg
                    or f"Co-authored-by: {GITHUB_USER} <" in msg
                )

            # Skip commits not by this user (merge commits, bots, other authors)
            if not is_commit_author and not is_coauthor:
                continue

            # Determine role
            if is_commit_author:
                role = "Implement" if pr["pr_author"] == GITHUB_USER else "Review & Implement"
            elif is_coauthor:
                role = "Review & Implement"
            else:
                continue  # Should not happen due to filter above

            all_commits.append({
                "sha": sha,
                "repo": pr["repo"],
                "repo_short": pr["repo"].split("/")[-1],
                "dt": dt,
                "date": dt.strftime("%Y-%m-%d") if dt else "??",
                "hour": dt.hour if dt else -1,
                "time": dt.strftime("%H:%M") if dt else "??:??",
                "msg": truncate(msg, 65),
                "pr": pr["number"],
                "pr_url": pr["url"],
                "pr_title": pr["title"],
                "pr_state": pr["state"],
                "is_merged": pr["merged_at"] is not None,
                "role": role,
                "commit_hash": sha[:8],
            })

    if not all_commits:
        print("\nNo commits found.")
        return

    # Sort newest first
    all_commits.sort(key=lambda c: (c["date"], c["time"]), reverse=True)

    width = 145

    # ── TABLE 1: Commit Log ──
    print(f"\n{'=' * width}")
    print(f"  COMMIT ACTIVITY LOG  |  {GITHUB_USER}  |  {ORG}  |  UTC+7")
    print(f"  Period: {since_label}  ->  {until_label}  |  {len(all_commits)} commits across {len(prs)} PRs")
    print(f"{'=' * width}")
    print(f"{'#':<4} {'Date':<12} {'Time':<6} {'Repo':<28} {'PR':<8} {'Role':<24} {'Message'}")
    print(f"{'~'*4} {'~'*11} {'~'*5} {'~'*27} {'~'*7} {'~'*23} {'~'*55}")

    for i, c in enumerate(all_commits, 1):
        sha_d = c["commit_hash"] or "—".ljust(8)
        pr_d = f"#{c['pr']}" if c["pr"] else "—"
        merged = " [M]" if c.get("is_merged") and c.get("commit_hash") else ""
        print(f"{i:<4} {c['date']:<12} {c['time']:<6} {c['repo_short']:<28} {pr_d:<8} {c['role']:<24} {c['msg']}{merged}")

    # ── TABLE 2: Hourly Summary ──
    if show_hours:
        print(f"\n{'─' * width}")
        print(f"  HOURLY BREAKDOWN (UTC+7)")
        print(f"{'─' * width}")

        by_dh = defaultdict(lambda: defaultdict(list))
        for c in all_commits:
            if c["hour"] >= 0:
                by_dh[c["date"]][c["hour"]].append(c)

        tot_hours = 0
        tot_commits = 0

        for date in sorted(by_dh):
            slots = by_dh[date]
            hrs = len(slots)
            day_c = sum(len(v) for v in slots.values())
            tot_hours += hrs
            tot_commits += day_c

            statuses = set(c["pr_state"] for c in slots.values() for c in [])
            
            print(f"\n  -- {date}  --  {hrs} active hour(s)  *  {day_c} commit(s)")

            for h in sorted(slots):
                items_h = slots[h]
                rc = defaultdict(int)
                for x in items_h:
                    rc[x["role"]] += 1
                roles_s = ", ".join(f"{r}:{n}" for r, n in sorted(rc.items()))
                prs_s = "  ".join(f"#{x['pr']}" if x["pr"] else "direct" for x in items_h)
                snippets = "  ".join(x["msg"][:40] for x in items_h[:3])

                print(f"      {h:02d}:00  |  {len(items_h):>2}  |  {roles_s:<30}  {prs_s}")
                print(f"              {snippets}")

        print(f"\n  {'~' * 70}")
        print(f"  TOTAL: {tot_hours} active hours  *  {tot_commits} commits  *  {len(by_dh)} day(s)")

    # ── TABLE 3: Per-PR Summary ──
    if show_pr:
        pr_map = defaultdict(lambda: {"role": "", "repo": "", "n": 0, "msgs": [], "url": "", "merged": False, "state": ""})

        for c in all_commits:
            if c["pr"]:
                k = c["pr"]
                pr_map[k]["role"] = c["role"]
                pr_map[k]["repo"] = c["repo_short"]
                pr_map[k]["n"] += 1
                pr_map[k]["msgs"].append(c["msg"])
                pr_map[k]["url"] = c["pr_url"]
                pr_map[k]["state"] = c.get("pr_state", "")
                if c.get("is_merged"):
                    pr_map[k]["merged"] = True

        sorted_prs = sorted(pr_map.items(), key=lambda x: -x[1]["n"])

        print(f"\n{'─' * width}")
        print(f"  PER-PR BREAKDOWN")
        print(f"{'─' * width}")
        
        merged_count = sum(1 for p in pr_map.values() if p.get("merged"))
        open_count = sum(1 for p in pr_map.values() if p.get("state") == "OPEN" and not p.get("merged"))
        
        print(f"  Merged: {merged_count}  |  Open: {open_count}  |  Total: {len(sorted_prs)} PRs\n")
        print(f"  {'PR':<10} {'Repo':<28} {'Status':<10} {'Role':<24} {'Count':<7} {'Commits'}")
        print(f"  {'~'*9} {'~'*27} {'~'*9} {'~'*23} {'~'*6} {'~'*50}")

        for pr_num, d in sorted_prs:
            merged_d = "[M]" if d.get("merged") else "[O]" if d.get("state") == "OPEN" else "[C]"
            msgs_s = "; ".join(d["msgs"][:2])
            if d["n"] > 2:
                msgs_s += f" (+{d['n'] - 2} more)"
            print(f"  #{pr_num:<9} {d['repo']:<28} {merged_d:<10} {d['role']:<24} {d['n']:<7} {msgs_s}")

    print(f"\n{'=' * width}")
    print("Done.")


if __name__ == "__main__":
    main()
