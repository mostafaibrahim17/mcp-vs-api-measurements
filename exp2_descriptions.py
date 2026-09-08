"""Experiment 2: do vague tool descriptions make the model pick the wrong tool?

Gives Claude Opus 5 the same 6 tools twice, once with descriptions written for a model and
once with the 1-line descriptions you get from generating tools off an API spec. Asks the
same 20 questions in each setup, 2 runs each, and counts how often the first tool call is
the right one.

Usage: ANTHROPIC_API_KEY=... python exp2_descriptions.py
"""
import anthropic

MODEL = "claude-opus-5"
RUNS = 2

SCHEMAS = {
    "fetch_page": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    "google_search": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    "amazon_search": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    "reddit_posts": {"type": "object", "properties": {"subreddit": {"type": "string"}}, "required": ["subreddit"]},
    "screenshot_page": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    "youtube_transcript": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
}

CLEAR = {
    "fetch_page": "Fetch the current text content of a specific public web page whose URL you already have. Use this to read documentation, articles, or pricing pages. Do not use it to search; use google_search when you do not have a URL.",
    "google_search": "Search the web with Google and return the top results with titles, URLs, and snippets. Use this when you need to find current information or a page whose URL you do not have.",
    "amazon_search": "Search Amazon for products and return names, prices, ratings, and availability. Use this for any question about what a product costs or whether it is in stock on Amazon.",
    "reddit_posts": "Return the most recent posts and top comments from a named subreddit. Use this for questions about what people on Reddit are saying or recommending.",
    "screenshot_page": "Render a public web page in a browser and return an image of how it looks. Use this only when the question is about the visual appearance or layout of a page, not its text.",
    "youtube_transcript": "Return the full spoken transcript of a YouTube video from its URL. Use this to summarize or answer questions about what is said in a video.",
}

VAGUE = {
    "fetch_page": "Gets data from the web.",
    "google_search": "Runs a search.",
    "amazon_search": "Works with Amazon.",
    "reddit_posts": "Works with Reddit.",
    "screenshot_page": "Takes a screenshot.",
    "youtube_transcript": "Works with YouTube.",
}

# (question, correct tool)
QUESTIONS = [
    ("Is the Sony WH-1000XM5 under $300 right now?", "amazon_search"),
    ("What are people in r/python saying about uv this week?", "reddit_posts"),
    ("What does https://decodo.com/pricing say the cheapest plan costs?", "fetch_page"),
    ("Show me what the homepage of https://stripe.com looks like at the moment.", "screenshot_page"),
    ("Summarize the main points of https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube_transcript"),
    ("Who won the Formula 1 race last weekend?", "google_search"),
    ("What is the current best-rated air fryer under $100?", "amazon_search"),
    ("What are the top posts on r/MachineLearning today?", "reddit_posts"),
    ("Read https://modelcontextprotocol.io/specification/latest and tell me the latest revision date.", "fetch_page"),
    ("Does the layout of https://news.ycombinator.com still use the orange header bar?", "screenshot_page"),
    ("What does the speaker say about pricing in https://www.youtube.com/watch?v=abc123xyz?", "youtube_transcript"),
    ("What was the closing price of NVIDIA stock yesterday?", "google_search"),
    ("Is the Kindle Paperwhite in stock, and how much is it?", "amazon_search"),
    ("What are redditors in r/homelab recommending for a cheap NAS?", "reddit_posts"),
    ("Pull the text of https://en.wikipedia.org/wiki/Model_Context_Protocol and give me the first paragraph.", "fetch_page"),
    ("Capture an image of https://www.apple.com so I can check the hero banner.", "screenshot_page"),
    ("Give me the transcript of the talk at https://youtu.be/xyz987", "youtube_transcript"),
    ("Which company announced a new open-source LLM this morning?", "google_search"),
    ("Compare Amazon prices for the Logitech MX Master 3S and the MX Master 3.", "amazon_search"),
    ("What is r/webscraping saying about Cloudflare blocks lately?", "reddit_posts"),
]

client = anthropic.Anthropic()
SYSTEM = "You are an assistant with tools. Answer by calling the single most appropriate tool first."


def run(descriptions, label):
    tools = [{"name": n, "description": descriptions[n], "input_schema": SCHEMAS[n]} for n in SCHEMAS]
    wrong = []
    total = 0
    for _ in range(RUNS):
        for q, expected in QUESTIONS:
            r = client.messages.create(model=MODEL, max_tokens=1024, system=SYSTEM, tools=tools, messages=[{"role": "user", "content": q}])
            use = next((b for b in r.content if b.type == "tool_use"), None)
            picked = use.name if use else "(no tool)"
            total += 1
            if picked != expected:
                wrong.append((q, expected, picked))
    print(f"\n{label}: {len(wrong)} wrong out of {total} ({100 * len(wrong) / total:.0f}%)")
    for q, e, p in wrong:
        print(f"  expected {e:18} got {p:18} | {q[:60]}")
    return len(wrong), total


# Variant: the same tools with the opaque names you get when tools are generated from an API spec.
OPAQUE = {"fetch_page": "get_content", "google_search": "get_results", "amazon_search": "get_items",
          "reddit_posts": "get_posts", "screenshot_page": "get_image", "youtube_transcript": "get_text"}


def run_opaque(descriptions, label):
    tools = [{"name": OPAQUE[n], "description": descriptions[n].replace("google_search", "get_results"), "input_schema": SCHEMAS[n]} for n in SCHEMAS]
    wrong = []
    total = 0
    for _ in range(RUNS):
        for q, expected in QUESTIONS:
            r = client.messages.create(model=MODEL, max_tokens=1024, system=SYSTEM, tools=tools, messages=[{"role": "user", "content": q}])
            use = next((b for b in r.content if b.type == "tool_use"), None)
            picked = use.name if use else "(no tool)"
            total += 1
            if picked != OPAQUE[expected]:
                wrong.append((q, OPAQUE[expected], picked))
    print(f"\n{label}: {len(wrong)} wrong out of {total} ({100 * len(wrong) / total:.0f}%)")
    for q, e, p in wrong:
        print(f"  expected {e:18} got {p:18} | {q[:60]}")


if __name__ == "__main__":
    run(CLEAR, "Descriptive names, clear descriptions")
    run(VAGUE, "Descriptive names, vague descriptions")
    run_opaque(CLEAR, "Spec-style names, clear descriptions")
    run_opaque(VAGUE, "Spec-style names, vague descriptions")
