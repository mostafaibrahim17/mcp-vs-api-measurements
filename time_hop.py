"""Time a Web Scraping API fetch directly vs through the MCP tool in scrape_server.py.
Usage: DECODO_USERNAME=... DECODO_PASSWORD=... python time_hop.py
"""
import json, os, statistics, subprocess, time, requests

u, p = os.environ["DECODO_USERNAME"], os.environ["DECODO_PASSWORD"]
URL = "https://news.ycombinator.com"
API = "https://scraper-api.decodo.com/v2/scrape"

srv = subprocess.Popen(["python", "scrape_server.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)


def rpc(msg, wait_id=None):
    srv.stdin.write(json.dumps(msg) + "\n"); srv.stdin.flush()
    if wait_id is None:
        return
    while True:
        m = json.loads(srv.stdout.readline())
        if m.get("id") == wait_id:
            return m


rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "bench", "version": "0"}}}, 1)
rpc({"jsonrpc": "2.0", "method": "notifications/initialized"})
s = requests.Session()
direct, mcp, i = [], [], 10
for _ in range(10):
    t = time.perf_counter(); s.post(API, json={"url": URL}, auth=(u, p), timeout=60); direct.append(time.perf_counter() - t)
    i += 1; t = time.perf_counter(); rpc({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": "fetch_page", "arguments": {"url": URL}}}, i); mcp.append(time.perf_counter() - t)
hop = []
for _ in range(20):
    i += 1; t = time.perf_counter(); rpc({"jsonrpc": "2.0", "id": i, "method": "tools/list"}, i); hop.append(time.perf_counter() - t)
srv.kill()
print(f"direct median {statistics.median(direct):.2f}s | mcp median {statistics.median(mcp):.2f}s | bare stdio round trip {1000*statistics.median(hop):.1f} ms")
