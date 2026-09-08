"""Step 3 of the registry survey: controls and counts on top of survey_results.jsonl.

  a. Echo control: every server that answered the legacy handshake with 2026-07-28 gets a second
     handshake asking for the nonsense version 1900-01-01. A server that echoes that back doesn't
     support anything in particular, so its 2026-07-28 answer is discounted.
  b. Token count: each unique tool list is counted once with Anthropic's free token counting API
     against Claude Opus 5, the way a client would send it (name, description, input_schema).

Writes survey_echo.json and survey_tokens.json.
Usage: ANTHROPIC_API_KEY=... python survey_followup.py
"""
import asyncio, json, hashlib, time, httpx, anthropic
from concurrent.futures import ThreadPoolExecutor

rows = [json.loads(l) for l in open("survey_results.jsonl")]
HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "MCP-Protocol-Version": "2025-11-25",
           "User-Agent": "mcp-vs-api-survey/1.0 (+decodo.com/blog; research probe)"}
BOGUS = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "1900-01-01", "capabilities": {}, "clientInfo": {"name": "survey", "version": "1.0"}}}


def parse(r):
    if "text/event-stream" in r.headers.get("content-type", ""):
        for line in r.text.splitlines():
            if line.startswith("data:"):
                try:
                    m = json.loads(line[5:].strip())
                    if "id" in m:
                        return m
                except Exception:
                    pass
        return None
    try:
        return json.loads(r.text)
    except Exception:
        return None


async def echo_control():
    targets = [r["url"] for r in rows if r["legacy_version"] == "2026-07-28"]
    sem = asyncio.Semaphore(60)
    out = {}

    async def one(client, url):
        async with sem:
            try:
                r = await client.post(url, json=BOGUS, headers=HEADERS)
                m = parse(r)
                out[url] = (m or {}).get("result", {}).get("protocolVersion") if m and "result" in m else ("error:" + str((m or {}).get("error", {}).get("message", ""))[:40] if m else f"http {r.status_code}")
            except Exception as e:
                out[url] = "exc:" + type(e).__name__

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False) as client:
        await asyncio.gather(*(one(client, u) for u in targets))
    json.dump(out, open("survey_echo.json", "w"))
    echoed = sum(1 for v in out.values() if v == "1900-01-01")
    print(f"echo control: {len(targets)} servers claimed 2026-07-28; {echoed} echoed a bogus version back; {len(targets) - echoed} held a real version list")


def token_counts():
    client = anthropic.Anthropic()
    base = client.messages.count_tokens(model="claude-opus-5", messages=[{"role": "user", "content": "hi"}]).input_tokens
    uniq = {}
    for r in rows:
        if r["tools"]:
            key = hashlib.sha1(json.dumps(r["tools"], sort_keys=True).encode()).hexdigest()
            uniq.setdefault(key, r["tools"])
    print(f"token count: {len(uniq)} unique tool lists to count")

    def count(item):
        key, tools = item
        t = [{"name": x["name"] or "tool", "description": (x["description"] or "")[:20000], "input_schema": x["inputSchema"] if isinstance(x["inputSchema"], dict) and x["inputSchema"].get("type") else {"type": "object"}} for x in tools]
        for attempt in range(4):
            try:
                n = client.messages.count_tokens(model="claude-opus-5", tools=t, messages=[{"role": "user", "content": "hi"}]).input_tokens - base
                return key, {"tools": len(tools), "tokens": n}
            except anthropic.RateLimitError:
                time.sleep(5 * (attempt + 1))
            except anthropic.BadRequestError as e:
                return key, {"tools": len(tools), "tokens": None, "error": str(e)[:80]}
            except Exception as e:
                time.sleep(2)
        return key, {"tools": len(tools), "tokens": None, "error": "gave up"}

    out = {}
    start = time.time()
    with ThreadPoolExecutor(max_workers=12) as ex:
        for i, (k, v) in enumerate(ex.map(count, uniq.items()), 1):
            out[k] = v
            if i % 500 == 0:
                print(f"  {i}/{len(uniq)} counted, {time.time() - start:.0f}s", flush=True)
    json.dump(out, open("survey_tokens.json", "w"))
    ok = [v for v in out.values() if v["tokens"] is not None]
    print(f"token count done: {len(ok)} lists counted, {len(out) - len(ok)} failed")


if __name__ == "__main__":
    asyncio.run(echo_control())
    token_counts()
