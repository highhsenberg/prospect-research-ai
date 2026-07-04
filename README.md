# AI Prospect Research Assistant

An AI-powered tool for prospect research and personalization. Give it a
prospect's public content (a blog post, company homepage, LinkedIn article),
and it:

1. Fetches and cleans the page text.
2. Scores every sentence and pulls out the strongest "hook" -- a specific,
   quotable stat or claim, instead of a generic summary.
3. Drafts a short, personalized outreach email built around that hook, using
   an LLM if you provide an API key, or a deterministic template if you
   don't (so the pipeline always runs, even offline / in CI).

This is the same category of tool behind real personalized outbound emails
that reference something specific and current about the prospect's own
public writing, rather than a generic templated blast. See
[`example_output.md`](./example_output.md) for a full run against a real
company homepage.

## Why hook-scoring instead of just "summarize the page"

A generic summary reads like a robot wrote it. A single, well-chosen stat or
contrarian line ("72% don't trust AI with live work") reads like someone
actually read the page. The scoring function in `research.py` prioritizes:

- Sentences containing a number or percentage (`_NUMBER_RE`)
- Sentences with contrast words (`but`, `only`, `despite`, `however`, ...)
- Sentences with superlatives (`most`, `first`, `never`, ...)
- Penalizes sentences that are too long to read naturally in an email

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python research.py \
  --url "https://example.com/blog/some-post" \
  --prospect-name "Jane Doe" \
  --company "Example Co" \
  --sender-name "Visal" \
  --sender-role "GTM engineer specializing in AI automation"
```

Optional: set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in your environment to
have the email drafted by an LLM instead of the built-in template.

## Project structure

```
research.py          -- fetch, score, and draft pipeline (single file, no server needed)
requirements.txt      -- runtime dependencies
example_output.md     -- real example run against a live company homepage
```

## Limitations / next steps

- Hook scoring is a lightweight heuristic (regex + keyword scoring), not a
  trained model -- it works well for stat-heavy marketing copy but can miss
  more subtle hooks in narrative writing.
- No de-duplication across multiple pages yet if you want to research a
  prospect across several URLs at once (blog + LinkedIn + about page).
- Batch mode (CSV of URLs in, CSV of drafts out) is a natural next step for
  running this across a full outbound list instead of one prospect at a time.
