# Measurements behind "MCP vs API"

Scripts and raw data for the numbers in the Decodo article. Results were collected on 2026-09-07.

- `probe_tools.py` – connects to an MCP server over stdio and saves its tools/list response. Example: `python probe_tools.py playwright npx -y @playwright/mcp@latest`
- `tools_*.json` – the raw tool lists captured from the filesystem, Playwright, Decodo, and GitHub servers
- `count_tokens.py` – counts the context tokens each tool list costs with Anthropic's token counting API
- `scrape_server.py` – the MCP server from the article, wrapping the Decodo Web Scraping API (needs the scrape_server.py credentials filled in; time_hop.py expects them in env instead)
- `time_hop.py` – times 10 fetches direct vs through the MCP tool, plus the bare stdio round trip

Install: `pip install mcp requests anthropic`
- `probe_version.py` – asks a server for the 2026-07-28 revision and records what it answers with
- `exp1_thinking_time.py` – times the model's turns against the tool call on 10 live questions
- `exp2_descriptions.py`, `exp2b_overcalling.py` – tool selection with clear vs vague descriptions, and unnecessary calls
- `exp3_injection.py` – planted instructions in fetched pages and in a tool description (all sandboxed, fake tools)

## Registry survey (2026-09-08)

- `survey_fetch_registry.py` – pulls every entry from the official registry and keeps unique public streamable HTTP endpoints (15,653)
- `survey_probe.py` – probes each endpoint: legacy handshake asking for 2026-07-28, tools/list when no login is needed, and the modern server/discover request. Writes `survey_results.jsonl` (large, not committed; rerun to regenerate)
- `survey_followup.py` – the echo control (ask for a made-up version and see who echoes it) and the free token count per unique tool list
- `survey_injection_hits.json` – descriptions flagged by the pattern screen, for hand review
- `survey_echo.json` – echo-control results

Findings used in the article: 7,904 of 15,653 answered; after removing 2 mass-publishing platforms and 403 echoers, 95% of 5,872 servers run a pre-2026 revision; 5,544 distinct tool lists with 73,189 tools; median 6 tools and ~1,900 tokens per server; 4,511 tool names shared by 2+ servers; collision chance 3% / 8% / 33% for 3 / 5 / 10 random servers.

## Survey data files

- `registry_remotes.json` – the 15,653 public streamable HTTP endpoints pulled from the registry on 2026-09-08
- `survey_endpoints.jsonl` – 1 line per endpoint: HTTP status, whether it needs a login, the protocol revision it answered with, whether it echoed a made-up version, whether it answers `server/discover`, server name and version, and tool count
- `survey_results.jsonl.gz` – the full per-endpoint results including every tool list collected (compressed; 128 MB uncompressed)
- `survey_echo.json` – raw echo-control answers for the 1,614 servers that claimed 2026-07-28
- `survey_injection_hits.json` – tool descriptions flagged by the pattern screen, for hand review
- `tools_*.json` – the 5 tool lists behind the token table in the article
