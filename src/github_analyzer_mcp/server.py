"""
GitHub Repository Analyzer MCP Server
Gives Claude deep analysis capabilities over any GitHub repository.
Tools: analyze_repo, get_contributors, find_issues, search_code,
       get_languages, analyze_commits, get_pull_requests, repo_health_score
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult,
)

# ── Server instance ────────────────────────────────────────────────────────────
app = Server("github-analyzer-mcp")

# ── GitHub API helper ──────────────────────────────────────────────────────────
GITHUB_API = "https://api.github.com"

def get_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

async def github_get(path: str, params: dict = None) -> dict | list:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{GITHUB_API}{path}",
            headers=get_headers(),
            params=params or {},
        )
        r.raise_for_status()
        return r.json()

def parse_repo(repo_arg: str) -> tuple[str, str]:
    """Parse 'owner/repo' or full GitHub URL."""
    repo_arg = repo_arg.strip().rstrip("/")
    if "github.com" in repo_arg:
        parts = repo_arg.split("github.com/")[-1].split("/")
        return parts[0], parts[1]
    parts = repo_arg.split("/")
    if len(parts) == 2:
        return parts[0], parts[1]
    raise ValueError(f"Invalid repo format: '{repo_arg}'. Use 'owner/repo'.")

def fmt_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def days_ago(iso_str: str) -> int:
    if not iso_str:
        return -1
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return -1

# ── Tool definitions ───────────────────────────────────────────────────────────
TOOLS = [
    Tool(
        name="analyze_repo",
        description=(
            "Get a comprehensive overview of a GitHub repository including stars, forks, "
            "description, topics, license, activity, and key metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository as 'owner/repo' or full GitHub URL",
                }
            },
            "required": ["repo"],
        },
    ),
    Tool(
        name="get_contributors",
        description="Get the top contributors to a repository with their commit counts.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository as 'owner/repo'"},
                "limit": {"type": "integer", "description": "Number of contributors (default 10)", "default": 10},
            },
            "required": ["repo"],
        },
    ),
    Tool(
        name="find_issues",
        description="Search open or closed issues in a repository with optional label filtering.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                "label": {"type": "string", "description": "Filter by label (e.g. 'bug', 'enhancement')"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["repo"],
        },
    ),
    Tool(
        name="search_code",
        description="Search for code patterns or keywords within a specific repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "query": {"type": "string", "description": "Code search query (e.g. 'def train_model', 'TODO', 'API_KEY')"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["repo", "query"],
        },
    ),
    Tool(
        name="get_languages",
        description="Get the programming languages used in a repository with percentage breakdown.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
            },
            "required": ["repo"],
        },
    ),
    Tool(
        name="analyze_commits",
        description="Analyze recent commit history — messages, authors, frequency, and patterns.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
                "branch": {"type": "string", "description": "Branch to analyze (default: main/master)"},
            },
            "required": ["repo"],
        },
    ),
    Tool(
        name="get_pull_requests",
        description="Get open or merged pull requests with review status and metadata.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["repo"],
        },
    ),
    Tool(
        name="repo_health_score",
        description=(
            "Generate a comprehensive health score (0-100) for a repository based on "
            "activity, documentation, community engagement, and maintenance signals."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
            },
            "required": ["repo"],
        },
    ),
]

# ── Tool handlers ──────────────────────────────────────────────────────────────
@app.list_tools()
async def list_tools() -> ListToolsResult:
    return ListToolsResult(tools=TOOLS)


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    try:
        if name == "analyze_repo":
            return await _analyze_repo(arguments)
        elif name == "get_contributors":
            return await _get_contributors(arguments)
        elif name == "find_issues":
            return await _find_issues(arguments)
        elif name == "search_code":
            return await _search_code(arguments)
        elif name == "get_languages":
            return await _get_languages(arguments)
        elif name == "analyze_commits":
            return await _analyze_commits(arguments)
        elif name == "get_pull_requests":
            return await _get_pull_requests(arguments)
        elif name == "repo_health_score":
            return await _repo_health_score(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True,
            )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True,
        )


async def _analyze_repo(args: dict) -> CallToolResult:
    owner, repo = parse_repo(args["repo"])
    data = await github_get(f"/repos/{owner}/{repo}")

    pushed = days_ago(data.get("pushed_at", ""))
    created = days_ago(data.get("created_at", ""))

    result = {
        "name": data["full_name"],
        "description": data.get("description") or "No description",
        "url": data["html_url"],
        "stars": fmt_number(data.get("stargazers_count", 0)),
        "forks": fmt_number(data.get("forks_count", 0)),
        "watchers": fmt_number(data.get("watchers_count", 0)),
        "open_issues": data.get("open_issues_count", 0),
        "default_branch": data.get("default_branch", "main"),
        "language": data.get("language") or "Not specified",
        "license": data.get("license", {}).get("name") if data.get("license") else "No license",
        "topics": data.get("topics", []),
        "size_kb": data.get("size", 0),
        "is_fork": data.get("fork", False),
        "is_archived": data.get("archived", False),
        "has_wiki": data.get("has_wiki", False),
        "has_discussions": data.get("has_discussions", False),
        "days_since_last_push": pushed,
        "days_since_created": created,
        "homepage": data.get("homepage") or None,
    }

    lines = [
        f"# {result['name']}",
        f"**Description:** {result['description']}",
        f"**URL:** {result['url']}",
        "",
        "## Stats",
        f"- ⭐ Stars: {result['stars']}",
        f"- 🍴 Forks: {result['forks']}",
        f"- 👁️ Watchers: {result['watchers']}",
        f"- 🐛 Open Issues: {result['open_issues']}",
        "",
        "## Metadata",
        f"- Language: {result['language']}",
        f"- License: {result['license']}",
        f"- Default branch: {result['default_branch']}",
        f"- Size: {result['size_kb']} KB",
        f"- Archived: {result['is_archived']}",
        f"- Last pushed: {result['days_since_last_push']} days ago",
        f"- Created: {result['days_since_created']} days ago",
    ]
    if result["topics"]:
        lines.append(f"- Topics: {', '.join(result['topics'])}")
    if result["homepage"]:
        lines.append(f"- Homepage: {result['homepage']}")

    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _get_contributors(args: dict) -> CallToolResult:
    owner, repo = parse_repo(args["repo"])
    limit = min(int(args.get("limit", 10)), 100)
    data = await github_get(f"/repos/{owner}/{repo}/contributors", {"per_page": limit})

    lines = [f"# Top {limit} Contributors — {owner}/{repo}", ""]
    for i, c in enumerate(data[:limit], 1):
        lines.append(f"{i}. **{c['login']}** — {fmt_number(c['contributions'])} commits  [{c['html_url']}]")

    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _find_issues(args: dict) -> CallToolResult:
    owner, repo = parse_repo(args["repo"])
    state = args.get("state", "open")
    label = args.get("label", "")
    limit = min(int(args.get("limit", 10)), 50)

    params: dict[str, Any] = {"state": state, "per_page": limit}
    if label:
        params["labels"] = label

    data = await github_get(f"/repos/{owner}/{repo}/issues", params)
    # Filter out pull requests (GitHub API includes PRs in issues endpoint)
    issues = [i for i in data if "pull_request" not in i][:limit]

    lines = [f"# {state.title()} Issues — {owner}/{repo}", f"Showing {len(issues)} issues", ""]
    for issue in issues:
        age = days_ago(issue.get("created_at", ""))
        labels = ", ".join(l["name"] for l in issue.get("labels", []))
        lines.append(f"### #{issue['number']}: {issue['title']}")
        lines.append(f"- State: {issue['state']} | Opened: {age} days ago | Comments: {issue.get('comments', 0)}")
        if labels:
            lines.append(f"- Labels: {labels}")
        lines.append(f"- URL: {issue['html_url']}")
        lines.append("")

    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _search_code(args: dict) -> CallToolResult:
    owner, repo = parse_repo(args["repo"])
    query = args["query"]
    limit = min(int(args.get("limit", 5)), 10)

    data = await github_get(
        "/search/code",
        {"q": f"{query} repo:{owner}/{repo}", "per_page": limit},
    )
    items = data.get("items", [])

    lines = [f"# Code Search: '{query}' in {owner}/{repo}", f"Total matches: {data.get('total_count', 0)}", ""]
    for item in items[:limit]:
        lines.append(f"### {item['path']}")
        lines.append(f"- URL: {item['html_url']}")
        if item.get("text_matches"):
            for match in item["text_matches"][:2]:
                fragment = match.get("fragment", "").replace("\n", " ").strip()[:200]
                lines.append(f"- Snippet: `{fragment}`")
        lines.append("")

    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _get_languages(args: dict) -> CallToolResult:
    owner, repo = parse_repo(args["repo"])
    data = await github_get(f"/repos/{owner}/{repo}/languages")

    total = sum(data.values()) or 1
    lines = [f"# Languages — {owner}/{repo}", ""]
    for lang, bytes_count in sorted(data.items(), key=lambda x: -x[1]):
        pct = bytes_count / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"**{lang}** {bar} {pct:.1f}% ({fmt_number(bytes_count)} bytes)")

    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _analyze_commits(args: dict) -> CallToolResult:
    owner, repo = parse_repo(args["repo"])
    limit = min(int(args.get("limit", 20)), 100)
    branch = args.get("branch", "")

    params: dict[str, Any] = {"per_page": limit}
    if branch:
        params["sha"] = branch

    data = await github_get(f"/repos/{owner}/{repo}/commits", params)

    authors: dict[str, int] = {}
    messages = []
    for c in data:
        author = c.get("commit", {}).get("author", {}).get("name", "Unknown")
        msg = c.get("commit", {}).get("message", "").split("\n")[0][:80]
        authors[author] = authors.get(author, 0) + 1
        messages.append((author, msg, days_ago(c.get("commit", {}).get("author", {}).get("date", ""))))

    lines = [f"# Commit Analysis — {owner}/{repo} (last {len(data)} commits)", ""]
    lines.append("## Top Committers")
    for author, count in sorted(authors.items(), key=lambda x: -x[1])[:5]:
        lines.append(f"- **{author}**: {count} commits")
    lines.append("")
    lines.append("## Recent Commits")
    for author, msg, age in messages[:10]:
        lines.append(f"- [{age}d ago] **{author}**: {msg}")

    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _get_pull_requests(args: dict) -> CallToolResult:
    owner, repo = parse_repo(args["repo"])
    state = args.get("state", "open")
    limit = min(int(args.get("limit", 10)), 50)

    data = await github_get(
        f"/repos/{owner}/{repo}/pulls",
        {"state": state, "per_page": limit},
    )

    lines = [f"# {state.title()} Pull Requests — {owner}/{repo}", f"Showing {len(data)} PRs", ""]
    for pr in data[:limit]:
        age = days_ago(pr.get("created_at", ""))
        lines.append(f"### #{pr['number']}: {pr['title']}")
        lines.append(f"- Author: {pr['user']['login']} | Opened: {age} days ago")
        lines.append(f"- Base: `{pr['base']['ref']}` ← Head: `{pr['head']['ref']}`")
        lines.append(f"- URL: {pr['html_url']}")
        lines.append("")

    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


async def _repo_health_score(args: dict) -> CallToolResult:
    owner, repo = parse_repo(args["repo"])

    # Fetch repo data + readme existence
    data = await github_get(f"/repos/{owner}/{repo}")
    try:
        await github_get(f"/repos/{owner}/{repo}/readme")
        has_readme = True
    except Exception:
        has_readme = False

    try:
        contribs = await github_get(f"/repos/{owner}/{repo}/contributors", {"per_page": 5})
        contributor_count = len(contribs)
    except Exception:
        contributor_count = 1

    # Scoring
    score = 0
    breakdown = []

    stars = data.get("stargazers_count", 0)
    s = min(int(stars / 100), 20)
    score += s
    breakdown.append(f"⭐ Stars ({stars}): +{s}/20")

    pushed = days_ago(data.get("pushed_at", ""))
    if pushed <= 7:    a = 20
    elif pushed <= 30: a = 15
    elif pushed <= 90: a = 8
    else:              a = 2
    score += a
    breakdown.append(f"📅 Activity (last push {pushed}d ago): +{a}/20")

    r = 15 if has_readme else 0
    score += r
    breakdown.append(f"📖 README exists: +{r}/15")

    lic = 10 if data.get("license") else 0
    score += lic
    breakdown.append(f"📄 License: +{lic}/10")

    issues = data.get("open_issues_count", 0)
    i = 10 if issues < 10 else (5 if issues < 50 else 2)
    score += i
    breakdown.append(f"🐛 Open issues ({issues}): +{i}/10")

    topics = len(data.get("topics", []))
    t = min(topics * 2, 10)
    score += t
    breakdown.append(f"🏷️ Topics ({topics}): +{t}/10")

    c = min(contributor_count * 3, 15)
    score += c
    breakdown.append(f"👥 Contributors ({contributor_count}): +{c}/15")

    if score >= 80:   grade = "A — Excellent"
    elif score >= 65: grade = "B — Good"
    elif score >= 50: grade = "C — Average"
    elif score >= 35: grade = "D — Needs work"
    else:             grade = "F — Poor"

    lines = [
        f"# Repository Health Score: {owner}/{repo}",
        f"## Overall Score: {score}/100 — Grade: {grade}",
        "",
        "## Breakdown",
    ] + breakdown + [
        "",
        "## Recommendations",
    ]

    if not has_readme:
        lines.append("- ❗ Add a detailed README with installation and usage instructions")
    if not data.get("license"):
        lines.append("- ❗ Add a license (MIT recommended for open source)")
    if topics < 3:
        lines.append("- 💡 Add more topics/tags to improve discoverability")
    if pushed > 90:
        lines.append("- ⚠️ Repository hasn't been updated in 90+ days — consider a maintenance update")
    if score >= 80:
        lines.append("- ✅ This repository is in great health! Keep up the maintenance.")

    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    asyncio.run(stdio_server(app))


if __name__ == "__main__":
    main()
