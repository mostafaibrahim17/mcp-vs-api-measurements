"""Build MCP-VS-API.html from MCP-VS-API.md so it copy-pastes cleanly into Google Docs.

- code blocks become 1-cell tables with inline monospace styling (survives a paste; <pre> does not)
- inline code gets an inline monospace font
- tables get inline borders
- the 5 PNGs are embedded as data URIs so images travel with the text

Run from the Agolia folder: python mcp-vs-api-measurements/build_article.py
"""
import base64, html, re, subprocess, sys

MD = "MCP-VS-API.md"
OUT = "MCP-VS-API.html"
TITLE = "MCP vs API: Understanding the Differences and Use Cases"
DESC = "Discover the key differences between MCP vs API, their roles in software integration, and how to choose the right solution for your project."

HEAD = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{html.escape(DESC)}">
<style>
  html,body{{background:#fff;color:#1a1a1a;margin:0}}
  body{{font:17px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  main{{max-width:760px;margin:0 auto;padding:48px 24px 96px}}
  h1{{font-size:2rem;line-height:1.2;margin:0 0 24px}}
  h2{{font-size:1.5rem;margin:48px 0 12px;border-bottom:1px solid #e5e5e5;padding-bottom:6px}}
  h3{{font-size:1.15rem;margin:32px 0 8px}}
  p,li{{margin:0 0 14px}}
  a{{color:#0a58ca}}
  img{{max-width:100%;height:auto;display:block;margin:0 0 20px;border:1px solid #e5e5e5;border-radius:6px}}
  blockquote{{border-left:4px solid #f0c040;background:#fff9e6;margin:0 0 20px;padding:10px 16px;color:#5a4a00}}
</style></head><body><main>
"""

body = subprocess.run(["pandoc", MD, "-f", "gfm", "-t", "html5", "--syntax-highlighting=none"], capture_output=True, text=True, check=True).stdout

MONO = "font-family:'Courier New',Menlo,monospace;font-size:10.5pt"


def code_table(m):
    inner = m.group(1)
    inner = re.sub(r"^<code[^>]*>", "", inner).rsplit("</code>", 1)[0]
    inner = inner.rstrip("\n").replace("\n", "<br>")
    return (f'<table style="border-collapse:collapse;width:100%;margin:0 0 20px"><tr><td style="background:#f1f3f4;'
            f'border:1px solid #dadce0;padding:12px 14px;{MONO};line-height:1.5;white-space:pre-wrap;word-break:break-word">{inner}</td></tr></table>')


body = re.sub(r"<pre[^>]*>(.*?)</pre>", code_table, body, flags=re.S)
body = re.sub(r"<code>(.*?)</code>", lambda m: f'<code style="{MONO};background:#f1f3f4;padding:1px 4px;border-radius:3px">{m.group(1)}</code>', body, flags=re.S)
body = body.replace("<table>", '<table style="border-collapse:collapse;margin:0 0 20px">')
body = re.sub(r"<(td|th)([^>]*)>", lambda m: f'<{m.group(1)}{m.group(2)} style="border:1px solid #ddd;padding:6px 10px;vertical-align:top">', body)


def embed(m):
    data = base64.b64encode(open(m.group(1), "rb").read()).decode()
    return f'src="data:image/png;base64,{data}"'


body = re.sub(r'src="(img-[^"]+\.png)"', embed, body)

open(OUT, "w").write(HEAD + body + "</main></body></html>")
print(f"built {OUT}: {len(body) / 1e6:.1f} MB, {body.count('data:image/png')} images, {body.count('white-space:pre-wrap')} code blocks")
