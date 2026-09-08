"""Count the context tokens each MCP server's tool list costs, using Anthropic's token counting API.
Usage: ANTHROPIC_API_KEY=... python count_tokens.py tools_*.json
"""
import json, sys, anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5"


def count(tools):
    t = [{"name": x["name"], "description": x.get("description", ""), "input_schema": x.get("inputSchema", {})} for x in tools]
    return client.messages.count_tokens(model=MODEL, tools=t, messages=[{"role": "user", "content": "hi"}]).input_tokens


base = client.messages.count_tokens(model=MODEL, messages=[{"role": "user", "content": "hi"}]).input_tokens
print(f"{'server':14} {'tools':>5} {'tokens':>7} {'per tool':>8}")
for f in sys.argv[1:]:
    tools = json.load(open(f))
    n = count(tools) - base
    print(f"{f[6:-5]:14} {len(tools):5} {n:7} {n // len(tools):8}")
