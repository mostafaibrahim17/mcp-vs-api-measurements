"""Experiment 2b: do weak descriptions make the model call tools it doesn't need?

Same 6 tools as exp2, clear vs vague descriptions, but the 10 questions here need no tool at all.
Counts how often the model calls a tool anyway. 2 runs each.
Usage: ANTHROPIC_API_KEY=... python exp2b_overcalling.py
"""
import anthropic
import exp2_descriptions as e

client = anthropic.Anthropic()
SYSTEM = "You are a helpful assistant. You have tools available. Use them when they are needed to answer."
NO_TOOL = [
    "What is 17 times 23?",
    "Who wrote Pride and Prejudice?",
    "Explain what a REST API is in 2 sentences.",
    "Convert 5 kilometers to miles.",
    "What is the capital of Australia?",
    "Write a haiku about autumn.",
    "What does HTTP status 404 mean?",
    "Give me a regular expression that matches a US ZIP code.",
    "What year did the Berlin Wall fall?",
    "Explain the difference between a list and a tuple in Python.",
]


def run(descriptions, label):
    tools = [{"name": n, "description": descriptions[n], "input_schema": e.SCHEMAS[n]} for n in e.SCHEMAS]
    called = []
    for _ in range(e.RUNS):
        for q in NO_TOOL:
            r = client.messages.create(model=e.MODEL, max_tokens=1024, system=SYSTEM, tools=tools, messages=[{"role": "user", "content": q}])
            use = next((b for b in r.content if b.type == "tool_use"), None)
            if use:
                called.append((q, use.name))
    print(f"\n{label}: unnecessary tool calls {len(called)} out of {e.RUNS * len(NO_TOOL)}")
    for q, n in called:
        print(f"  called {n:18} | {q}")


if __name__ == "__main__":
    run(e.CLEAR, "Clear descriptions")
    run(e.VAGUE, "Vague descriptions")
