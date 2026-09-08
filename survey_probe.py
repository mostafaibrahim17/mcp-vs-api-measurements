"""Step 2 of the registry survey: probe every public streamable HTTP endpoint from registry_remotes.json.

For each endpoint, at most 3 small POSTs:
  1. a legacy `initialize` asking for protocol 2026-07-28 (a legacy server answers with the newest
     revision it supports; a modern server rejects it)
  2. `notifications/initialized` + `tools/list` when the handshake succeeded without auth
  3. a modern `server/discover` carrying 2026-07-28 request metadata

Appends one JSON line per endpoint to survey_results.jsonl. Safe to re-run; already-probed URLs are skipped.
"""
import asyncio, json, os, sys, time, httpx

IN, OUT = "registry_remotes.json", "survey_results.jsonl"
CONCURRENCY, TIMEOUT = 60, 15.0
HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json",
           "MCP-Protocol-Version": "2026-07-28", "User-Agent": "mcp-vs-api-survey/1.0 (+decodo.com/blog; research probe, 3 requests max)"}

INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2026-07-28", "capabilities": {}, "clientInfo": {"name": "survey", "version": "1.0"}}}
INITIALIZED = {"jsonrpc": "2.0", "method": "notifications/initialized"}
TOOLS = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientInfo": {"name": "survey", "version": "1.0"}, "io.modelcontextprotocol/clientCapabilities": {}}
DISCOVER = {"jsonrpc": "2.0", "id": 3, "method": "server/discover", "params": {"_meta": META}}


def parse_body(r):
    ct = r.headers.get("content-type", "")
    text = r.text
    if "text/event-stream" in ct:
        for line in text.splitlines():
            if line.startswith("data:"):
                try:
                    m = json.loads(line[5:].strip())
                    if "id" in m:
                        return m
                except Exception:
                    pass
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


async def probe(client, rec, sem):
    url = rec["url"]
    out = {"url": url, "name": rec["name"], "http": None, "auth": False, "legacy_version": None, "server": None,
           "modern": False, "tools": None, "error": None}
    async with sem:
        try:
            r = await client.post(url, json=INIT, headers=HEADERS)
            out["http"] = r.status_code
            if r.status_code in (401, 403):
                out["auth"] = True
            elif r.status_code < 500:
                m = parse_body(r)
                if m and "result" in m:
                    res = m["result"]
                    out["legacy_version"] = res.get("protocolVersion")
                    si = res.get("serverInfo") or {}
                    out["server"] = f"{si.get('name', '')} {si.get('version', '')}".strip()
                    sid = r.headers.get("mcp-session-id")
                    h = dict(HEADERS)
                    h["MCP-Protocol-Version"] = out["legacy_version"] or "2025-11-25"
                    if sid:
                        h["Mcp-Session-Id"] = sid
                    try:
                        await client.post(url, json=INITIALIZED, headers=h)
                        t = await client.post(url, json=TOOLS, headers=h)
                        tm = parse_body(t)
                        if tm and "result" in tm:
                            out["tools"] = [{"name": x.get("name"), "description": x.get("description", "") or "", "inputSchema": x.get("inputSchema", {})} for x in tm["result"].get("tools", [])]
                    except Exception as e:
                        out["error"] = f"tools: {type(e).__name__}"
                elif m and "error" in m:
                    out["error"] = f"init: {str(m['error'].get('message', ''))[:80]}"
            # modern probe
            try:
                d = await client.post(url, json=DISCOVER, headers=HEADERS)
                dm = parse_body(d)
                if dm and "result" in dm and isinstance(dm["result"], dict) and ("protocolVersions" in dm["result"] or "supportedVersions" in dm["result"] or "versions" in dm["result"]):
                    out["modern"] = True
                    out["discover"] = dm["result"]
            except Exception:
                pass
        except httpx.TimeoutException:
            out["error"] = "timeout"
        except Exception as e:
            out["error"] = type(e).__name__
    return out


async def main():
    recs = json.load(open(IN))
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            try:
                done.add(json.loads(line)["url"])
            except Exception:
                pass
    todo = [r for r in recs if r["url"] not in done]
    print(f"{len(todo)} endpoints to probe ({len(done)} already done)", flush=True)
    sem = asyncio.Semaphore(CONCURRENCY)
    start = time.time()
    f = open(OUT, "a")
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, verify=False) as client:
        tasks = [probe(client, r, sem) for r in todo]
        n = 0
        for coro in asyncio.as_completed(tasks):
            out = await coro
            f.write(json.dumps(out) + "\n"); f.flush()
            n += 1
            if n % 250 == 0:
                print(f"{n}/{len(todo)} done, {time.time() - start:.0f}s", flush=True)
    f.close()
    print(f"finished {n} in {time.time() - start:.0f}s", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
