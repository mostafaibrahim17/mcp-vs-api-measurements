import requests
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

import os
scraping_username = os.environ.get("DECODO_USERNAME", "YOUR_SCRAPING_USERNAME")
scraping_password = os.environ.get("DECODO_PASSWORD", "YOUR_SCRAPING_PASSWORD")
SCRAPE_URL = "https://scraper-api.decodo.com/v2/scrape"

server = MCPServer("live-web")


@server.tool()
def fetch_page(url: str, render_js: bool = False) -> str:
    """Fetch the current content of a public web page and return it as text.
    Use this when the answer depends on information that may have changed
    since your training data, such as prices, headlines, or documentation.
    Set render_js to true only for pages that load their content with JavaScript."""
    payload = {"url": url, "markdown": True}
    if render_js:
        payload["headless"] = "html"  # render the page in a browser before returning it
    response = requests.post(SCRAPE_URL, json=payload, auth=(scraping_username, scraping_password), timeout=60)
    if response.status_code != 200:
        raise ToolError(f"The scraping API returned status {response.status_code} for {url}")
    return response.json()["results"][0]["content"]


if __name__ == "__main__":
    server.run(transport="stdio")
