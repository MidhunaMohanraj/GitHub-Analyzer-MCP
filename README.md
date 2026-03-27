# 🔌 GitHub Repository Analyzer MCP

<div align="center">

![Banner](https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,10,18&height=180&section=header&text=GitHub%20Analyzer%20MCP&fontSize=42&fontColor=fff&animation=twinkling&fontAlignY=38&desc=Give%20Claude%20deep%20GitHub%20superpowers%20%7C%20Model%20Context%20Protocol%20Server&descAlignY=58&descSize=14)

<p>
  <img src="https://img.shields.io/badge/MCP-Model%20Context%20Protocol-7c3aed?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Claude-Compatible-f97316?style=for-the-badge&logo=anthropic&logoColor=white"/>
  <img src="https://img.shields.io/badge/PyPI-github--analyzer--mcp-3776AB?style=for-the-badge&logo=pypi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge"/>
</p>

<p>
  <b>An MCP server that gives Claude 8 powerful GitHub analysis tools — analyze any repo, score its health, find issues, search code, and more — directly inside Claude Desktop.</b>
</p>

</div>

---

## 🌟 What This Does

Once installed, you can ask Claude things like:

> *"Analyze the health of the langchain repo"*
> *"Who are the top contributors to pytorch/pytorch?"*
> *"Find all open bug issues in fastapi"*
> *"Search for TODO comments in microsoft/vscode"*
> *"What languages does the Next.js repo use?"*
> *"Show me recent commits to the main branch of tensorflow"*

Claude uses this MCP server to fetch real GitHub data and give you deep, structured analysis.

---

## 🛠️ Available Tools

| Tool | Description |
|---|---|
| `analyze_repo` | Full repo overview — stars, forks, metadata, activity |
| `get_contributors` | Top contributors with commit counts |
| `find_issues` | Open/closed issues with label filtering |
| `search_code` | Find code patterns across a repo |
| `get_languages` | Language breakdown with percentages |
| `analyze_commits` | Recent commit history and author patterns |
| `get_pull_requests` | Open/merged PRs with review metadata |
| `repo_health_score` | 0-100 health score with improvement suggestions |

---

## 📦 Installation

### Option 1 — pip (recommended)

```bash
pip install github-analyzer-mcp
```

### Option 2 — from source

```bash
git clone https://github.com/MidhunaMohanraj/github-analyzer-mcp
cd github-analyzer-mcp
pip install -e .
```

---

## ⚙️ Claude Desktop Configuration

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "github-analyzer": {
      "command": "github-analyzer-mcp",
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

Then **restart Claude Desktop**. You'll see the GitHub tools available in Claude's tool panel.

### GitHub Token (optional but recommended)

Without a token: 60 requests/hour limit.
With a token: 5,000 requests/hour + access to private repos.

Get a free token at: **github.com/settings/tokens** → Generate new token (classic) → check `public_repo` scope.

---

## 🧪 Test Locally

```bash
# Set token (optional)
export GITHUB_TOKEN=your_token_here

# Run the server directly
github-analyzer-mcp

# Or test with MCP inspector
npx @modelcontextprotocol/inspector github-analyzer-mcp
```

---

## 💬 Example Claude Conversations

**Repo health check:**
> You: *"Give me a health score for the huggingface/transformers repo"*
> Claude: *Uses `repo_health_score` → Returns 87/100, Grade A, with specific recommendations*

**Code search:**
> You: *"Search for all uses of 'deprecated' in the requests library"*
> Claude: *Uses `search_code` → Returns file locations and code snippets*

**Contributor analysis:**
> You: *"Who are the top 5 contributors to kubernetes/kubernetes?"*
> Claude: *Uses `get_contributors` → Returns ranked list with commit counts*

---

## 📁 Project Structure

```
github-analyzer-mcp/
├── src/github_analyzer_mcp/
│   ├── __init__.py
│   └── server.py          # 8 MCP tools
├── pyproject.toml          # PyPI config
├── README.md
└── LICENSE
```

---

## 🗺️ Roadmap

- [ ] Repository comparison tool (compare two repos side-by-side)
- [ ] GitHub Actions workflow analyzer
- [ ] Security vulnerability scanner via GitHub Advisory API
- [ ] Dependency graph analyzer
- [ ] Release history and changelog summarizer

---

## 🤝 Contributing

PRs welcome! Open an issue first to discuss major changes.

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Built with ❤️ using [MCP](https://modelcontextprotocol.io) · Compatible with Claude Desktop

![Footer](https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,10,18&height=80&section=footer)

</div>
