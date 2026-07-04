#!/usr/bin/env python3
"""
AI Prospect Research Assistant
--------------------------------
Given a prospect's public content (a blog post, LinkedIn article, or any URL),
this tool:

1. Fetches and cleans the page text.
2. Extracts the strongest "hook" -- a specific, quotable stat or claim that a
   human researcher would normally have to skim the whole page to find.
3. Drafts a short, personalized outreach email that references the hook
   naturally, instead of a generic templated blast.

This is the same category of tool used to draft the outbound email referencing
Maybe*'s "AI Confidence Crisis" post -- see example_output.md for that exact run.

Usage:
    python research.py --url "https://example.com/blog/some-post" \\
        --prospect-name "Jane Doe" \\
        --company "Example Co" \\
        --sender-name "Visal" \\
        --sender-role "GTM engineer specializing in AI automation"

If ANTHROPIC_API_KEY or OPENAI_API_KEY is set in the environment, the email
is drafted by an LLM. Otherwise the tool falls back to a deterministic
template so the pipeline is still fully runnable offline / in CI.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

USER_AGENT = "ProspectResearchAssistant/1.0 (+https://visalnkr.com)"


# --------------------------------------------------------------------------
# 1. Fetch + clean page content
# --------------------------------------------------------------------------

def fetch_page_text(url: str, timeout: int = 15) -> str:
    """Download a URL and return readable article text (tags stripped)."""
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Drop obviously non-article elements before extracting text.
    for tag in soup(["script", "style", "nav", "footer", "header", "form", "noscript"]):
        tag.decompose()

    # Prefer <article> / <main> if present, else fall back to <body>.
    container = soup.find("article") or soup.find("main") or soup.body or soup

    text = container.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text


# --------------------------------------------------------------------------
# 2. Hook extraction
# --------------------------------------------------------------------------

@dataclass
class Hook:
    sentence: str
    score: float


_NUMBER_RE = re.compile(r"\b\d{1,3}(?:[.,]\d+)?%|\b\d[\d,]{2,}\b")
_CONTRAST_WORDS = {"but", "yet", "however", "only", "just", "actually", "despite"}
_SUPERLATIVE_WORDS = {"most", "least", "first", "only", "never", "biggest", "smallest"}


def _split_sentences(text: str) -> List[str]:
    # Lightweight sentence splitter -- good enough for hook-mining, avoids a
    # heavy NLP dependency for what is otherwise a small utility.
    raw = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in raw if 25 <= len(s.strip()) <= 240]


def _score_sentence(sentence: str) -> float:
    score = 0.0
    lower = sentence.lower()

    if _NUMBER_RE.search(sentence):
        score += 3.0  # stats are the strongest hooks

    words = set(re.findall(r"[a-z']+", lower))
    score += 1.0 * len(words & _CONTRAST_WORDS)
    score += 0.5 * len(words & _SUPERLATIVE_WORDS)

    # Mild penalty for very long sentences -- they read poorly when quoted.
    if len(sentence) > 180:
        score -= 1.0

    return score


def extract_hooks(text: str, top_n: int = 3) -> List[Hook]:
    """Return the top_n most quotable sentences from a page of text."""
    candidates = [Hook(s, _score_sentence(s)) for s in _split_sentences(text)]
    candidates = [c for c in candidates if c.score > 0]
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:top_n]


# --------------------------------------------------------------------------
# 3. Email drafting
# --------------------------------------------------------------------------

TEMPLATE = """Hi {prospect_name},

I came across {company}'s work and this line stopped me: "{hook}"

I'm {sender_name}, {sender_role}. That stat is exactly the kind of gap I spend
my time closing -- turning it from an interesting insight into something a
team can actually act on.

Worth a quick 15-minute conversation to see if there's a fit?

Best,
{sender_name}
"""


def draft_email_with_llm(prospect_name: str, company: str, hook: str,
                          sender_name: str, sender_role: str) -> Optional[str]:
    """Draft the email with an LLM if an API key is available, else None."""
    prompt = (
        f"Write a short (under 120 words), specific, non-generic cold email.\n"
        f"Prospect name: {prospect_name}\n"
        f"Prospect company: {company}\n"
        f"Hook to reference naturally (do not quote it verbatim in full): {hook}\n"
        f"Sender name: {sender_name}\n"
        f"Sender role: {sender_role}\n"
        f"End with a soft ask for a 15-minute call. Sign off with the sender name only."
    )

    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # type: ignore

            client = anthropic.Anthropic()
            resp = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip()
        except Exception as exc:  # pragma: no cover - network/env dependent
            print(f"[warn] Anthropic call failed, falling back to template: {exc}", file=sys.stderr)

    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI()
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:  # pragma: no cover - network/env dependent
            print(f"[warn] OpenAI call failed, falling back to template: {exc}", file=sys.stderr)

    return None


def draft_email(prospect_name: str, company: str, hook: str,
                 sender_name: str, sender_role: str) -> str:
    llm_result = draft_email_with_llm(prospect_name, company, hook, sender_name, sender_role)
    if llm_result:
        return llm_result

    return TEMPLATE.format(
        prospect_name=prospect_name,
        company=company,
        hook=hook,
        sender_name=sender_name,
        sender_role=sender_role,
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="AI Prospect Research Assistant")
    parser.add_argument("--url", required=True, help="URL of the prospect's public content")
    parser.add_argument("--prospect-name", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--sender-name", default="Visal")
    parser.add_argument("--sender-role", default="GTM engineer specializing in AI automation")
    parser.add_argument("--top-hooks", type=int, default=3, help="How many candidate hooks to show")
    args = parser.parse_args()

    print(f"Fetching {args.url} ...")
    text = fetch_page_text(args.url)

    hooks = extract_hooks(text, top_n=args.top_hooks)
    if not hooks:
        print("No strong hooks found -- falling back to first sentence of the page.")
        best_hook = _split_sentences(text)[0] if _split_sentences(text) else text[:150]
    else:
        print("\nTop candidate hooks:")
        for i, h in enumerate(hooks, 1):
            print(f"  {i}. (score {h.score:.1f}) {h.sentence}")
        best_hook = hooks[0].sentence

    email = draft_email(
        prospect_name=args.prospect_name,
        company=args.company,
        hook=best_hook,
        sender_name=args.sender_name,
        sender_role=args.sender_role,
    )

    print("\n--- Drafted email ---\n")
    print(email)


if __name__ == "__main__":
    main()
