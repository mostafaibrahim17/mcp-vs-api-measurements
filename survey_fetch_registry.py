"""Step 1 of the registry survey: pull every server entry from the official MCP registry and keep the
latest active version of each server that has a streamable HTTP remote endpoint.

Writes registry_remotes.json: one record per unique endpoint URL.
"""
import json, time, urllib.parse, urllib.request

BASE = "https://registry.modelcontextprotocol.io/v0/servers"
servers = {}
cursor = None
pages = 0
while True:
    q = {"limit": 100}
    if cursor:
        q["cursor"] = cursor
    with urllib.request.urlopen(BASE + "?" + urllib.parse.urlencode(q), timeout=60) as r:
        d = json.load(r)
    for e in d["servers"]:
        s, m = e["server"], e["_meta"]["io.modelcontextprotocol.registry/official"]
        if m.get("status") != "active" or not m.get("isLatest"):
            continue
        for rem in s.get("remotes", []) or []:
            if rem.get("type") == "streamable-http" and rem.get("url", "").startswith("https://"):
                url = rem["url"].rstrip("/")
                servers.setdefault(url, {"url": url, "name": s["name"], "title": s.get("title", ""), "version": s.get("version", ""), "published": m.get("publishedAt", "")[:10]})
    pages += 1
    cursor = d.get("metadata", {}).get("nextCursor")
    if not cursor:
        break
    time.sleep(0.2)
json.dump(list(servers.values()), open("registry_remotes.json", "w"), indent=1)
print(f"pages {pages}, unique streamable HTTP endpoints from latest active versions: {len(servers)}")
