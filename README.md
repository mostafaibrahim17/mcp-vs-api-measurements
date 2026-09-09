# MCP vs API: the measurements

Scripts and data behind the article **MCP vs API: Understanding the Differences and Use Cases**, forthcoming on the Decodo blog at [decodo.com/blog/mcp-vs-api](https://decodo.com/blog/mcp-vs-api). The link goes live when the article is published.

Every number in the article that isn't quoted from a spec was produced by something in this folder. You can rerun all of it. Nothing here needs a paid API call except the 4 model experiments, which cost a few dollars in total.

---

## Headline findings

All measurements were taken on **8 September 2026**.

| Question | What we did | What we found |
| :--- | :--- | :--- |
| What does a tool list cost in context? | Counted the tool definitions of 4 public servers with Anthropic's token counter | 222 to 448 tokens per tool. GitHub's full toolset is 39,836 tokens, 20% of a 200K window |
| Is MCP slower than calling the API directly? | Fetched the same page 10 times each way, then timed a model driving the tool on 10 live questions | The MCP hop is under 1 ms. The model's own turns were 71% of the wait |
| Has anyone shipped the 2026-07-28 spec revision? | Probed all 15,653 public endpoints in the official registry | 95% of 5,872 answering servers still run a 2025 revision. 288 support the new one |
| Do vague tool descriptions cause wrong tool calls? | 6 distinct tools, 20 questions, 200 calls, 4 description styles | 0 wrong picks. Descriptions decide only when tools overlap |
| How common is tool overlap? | Compared tool names across 5,544 registry servers | 4,511 names are shared by 2+ servers. 10 random servers give a 33% collision chance |
| Does prompt injection through MCP work today? | 20 planted page instructions and 20 poisoned-description calls against Claude Opus 5 | 0 leaks. In 2 of 5 injection styles the model returned a blank reply instead of an answer |
| Do real servers put instructions in descriptions? | Screened 110,979 descriptions from the registry | None malicious. 36 order the model to call them first, some in capitals |

---

## Reproducing the results

### Requirements

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install mcp requests anthropic httpx
```

Python 3.11 or newer. Tested with `mcp` 2.2.0. Node.js is needed only to run the public MCP servers through `npx`, and Docker only for GitHub's server.

Credentials are read from environment variables and never appear in the code:

| Variable | Used by | Where to get it |
| :--- | :--- | :--- |
| `DECODO_USERNAME`, `DECODO_PASSWORD` | `scrape_server.py`, `time_hop.py`, `exp1_thinking_time.py` | Web Scraping API section of the Decodo dashboard |
| `ANTHROPIC_API_KEY` | `count_tokens.py`, `exp1` to `exp3`, `survey_followup.py` | platform.claude.com/settings/keys |

### 1. Token cost of a tool list

```bash
python probe_tools.py playwright npx -y @playwright/mcp@latest
python probe_tools.py filesystem npx -y @modelcontextprotocol/server-filesystem /tmp
python count_tokens.py tools_*.json
```

The first command connects to a server over stdio and saves its `tools/list` answer. The second counts the tokens a client would send to the model for each saved list. Token counting is free.

### 2. Latency: the hop and the model

```bash
python time_hop.py            # 10 direct fetches vs 10 through the MCP tool, plus the bare stdio round trip
python exp1_thinking_time.py  # 10 live questions to Claude Opus 5 with the tool attached, timed per part
```

### 3. Registry survey

```bash
python survey_fetch_registry.py   # pulls the registry, writes registry_remotes.json (15,653 endpoints)
python survey_probe.py            # probes every endpoint, writes survey_results.jsonl (about 16 minutes)
python survey_followup.py         # echo control, then free token counts for every unique tool list
python probe_version.py ours python scrape_server.py   # ask any single server which revision it speaks
```

Each endpoint receives at most 3 small requests: a handshake asking for revision 2026-07-28, a `tools/list` request when no login is needed, and a `server/discover` request. The echo control asks every server that claimed 2026-07-28 for a made-up version and discounts the ones that echo it back.

### 4. Description and injection experiments

```bash
python exp2_descriptions.py    # clear vs vague descriptions, descriptive vs spec-style names
python exp2b_overcalling.py    # do vague descriptions cause tool calls on questions that need none
python exp3_injection.py       # planted page instructions and a poisoned tool description
```

Everything in `exp3` is sandboxed. The "tools" are fakes that record what the model asked for. Nothing is sent anywhere and no page is fetched.

---

## The example server

`scrape_server.py` is the MCP server built in the article. It exposes 1 tool, `fetch_page`, which wraps the Decodo Web Scraping API and returns a page as Markdown.

```bash
python scrape_server.py                                         # runs over stdio, waits for a client
npx @modelcontextprotocol/inspector python scrape_server.py     # inspect it in a browser
```

---

## Data files

| File | Contents |
| :--- | :--- |
| `registry_remotes.json` | The 15,653 public streamable HTTP endpoints, with registry name, version, and publish date |
| `survey_endpoints.jsonl` | 1 line per endpoint: HTTP status, login required, revision answered, echo-control result, `server/discover` support, server name, tool count |
| `survey_results.jsonl.gz` | The full probe output including every tool list collected. 128 MB uncompressed |
| `survey_echo.json` | Raw echo-control answers for the 1,614 servers that claimed 2026-07-28 |
| `survey_injection_hits.json` | Tool descriptions flagged by the pattern screen, grouped by pattern, for hand review |
| `tools_*.json` | The 5 tool lists behind the token table: filesystem, Playwright, Decodo, GitHub default, GitHub all |

---

## Notes on method

- **Dedupe.** Two platforms publish over 1,000 near-identical servers each. The survey statistics remove them so 2 vendors don't stand in for the ecosystem. The raw data keeps everything.
- **Echo control.** 403 servers answered "2026-07-28" and also answered "1900-01-01" when asked. They're excluded from the version counts.
- **Token counts.** The 5 servers in the article's table were counted with Anthropic's official endpoint. The registry-wide token figures use a tokenizer estimate scaled by the ratio measured on those 5, and the article labels them as estimates.
- **Sample sizes.** The model experiments are 10 to 200 calls each on 1 model on 1 day. They show what happened, not what always happens.

---

## Article assets

`hero.html` and `diagrams.html` are the source for the article's thumbnail and 2 diagrams. `build_article.py` turns the article's Markdown into a paste-ready HTML page with the images embedded.
