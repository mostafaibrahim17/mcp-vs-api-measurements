"""Experiment 1: where does the time go in an MCP tool call driven by a model?

Runs 10 questions through Claude Opus 5 with the fetch_page tool attached. For each
question we time 3 things separately:
  model    – the 2 model calls (decide to call the tool, then answer from the result)
  tool     – the tools/call round trip to scrape_server.py over stdio, which includes the fetch
  total    – wall clock from question to final answer

Usage: ANTHROPIC_API_KEY=... DECODO_USERNAME=... DECODO_PASSWORD=... python exp1_thinking_time.py
"""
import json, statistics, subprocess, sys, time
import anthropic

MODEL = "claude-opus-5"
QUESTIONS = [
    "What is the top story on https://news.ycombinator.com right now?",
    "How many stories on the front page of https://news.ycombinator.com have more than 100 points?",
    "What is the current top headline on https://www.bbc.com/news?",
    "What does https://ip.decodo.com say?",
    "What is the title of the newest post on https://blog.python.org?",
    "Which repositories are trending today on https://github.com/trending?",
    "What is the latest release version listed on https://pypi.org/project/requests/?",
    "What is the top headline on https://www.reuters.com right now?",
    "What does the page https://modelcontextprotocol.io say MCP is, in 1 sentence?",
    "What is the price of the first product shown on https://books.toscrape.com?",
]

TOOL = {
    "name": "fetch_page",
    "description": "Fetch the current content of a public web page and return it as text. Use this when the answer depends on information that may have changed since your training data, such as prices, headlines, or documentation. Set render_js to true only for pages that load their content with JavaScript.",
    "input_schema": {
        "type": "object",
        "properties": {"url": {"type": "string"}, "render_js": {"type": "boolean", "default": False}},
        "required": ["url"],
    },
}

srv = subprocess.Popen([sys.executable, "scrape_server.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)


def rpc(msg, wait_id=None):
    srv.stdin.write(json.dumps(msg) + "\n"); srv.stdin.flush()
    if wait_id is None:
        return
    while True:
        m = json.loads(srv.stdout.readline())
        if m.get("id") == wait_id:
            return m


rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "exp1", "version": "0"}}}, 1)
rpc({"jsonrpc": "2.0", "method": "notifications/initialized"})

client = anthropic.Anthropic()
rows = []
for i, q in enumerate(QUESTIONS, start=10):
    t0 = time.perf_counter()
    messages = [{"role": "user", "content": q}]
    t = time.perf_counter()
    first = client.messages.create(model=MODEL, max_tokens=4096, tools=[TOOL], messages=messages)
    model_1 = time.perf_counter() - t
    uses = [b for b in first.content if b.type == "tool_use"]
    if not uses:
        print(f"{i-9:2}. no tool call ({first.stop_reason})"); continue
    t = time.perf_counter()
    results = []
    for k, use in enumerate(uses):
        res = rpc({"jsonrpc": "2.0", "id": i * 10 + k, "method": "tools/call", "params": {"name": use.name, "arguments": use.input}}, i * 10 + k)
        results.append({"type": "tool_result", "tool_use_id": use.id, "content": res["result"]["content"][0]["text"][:60000]})
    tool_s = time.perf_counter() - t
    messages.append({"role": "assistant", "content": first.content})
    messages.append({"role": "user", "content": results})
    t = time.perf_counter()
    second = client.messages.create(model=MODEL, max_tokens=4096, tools=[TOOL], messages=messages)
    model_2 = time.perf_counter() - t
    total = time.perf_counter() - t0
    answer = next((b.text for b in second.content if b.type == "text"), "").replace("\n", " ")[:80]
    rows.append((model_1 + model_2, tool_s, total))
    print(f"{i-9:2}. model {model_1 + model_2:5.2f}s  tool {tool_s:5.2f}s ({len(uses)} call)  total {total:5.2f}s  | {answer}")

srv.kill()
m = [r[0] for r in rows]; tl = [r[1] for r in rows]; tt = [r[2] for r in rows]
print(f"\nmedian: model {statistics.median(m):.2f}s  tool (fetch + hop) {statistics.median(tl):.2f}s  total {statistics.median(tt):.2f}s")
print(f"model share of total: {100 * sum(m) / sum(tt):.0f}%")
