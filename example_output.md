# Example run

```
$ python research.py --url "https://www.maybetech.com/" \
    --prospect-name "Polly" \
    --company "Maybe*" \
    --sender-name "Visal" \
    --sender-role "GTM engineer specializing in AI automation"

Fetching https://www.maybetech.com/ ...

Top candidate hooks:
  1. (score 3.0) 72% Don't Trust AI With Live Work AI is tested in isolation, but blocked from real workflows.
  2. (score 3.0) 65% Lack Clear AI Ownership Pilots succeed, but accountability breaks after launch.
  3. (score 3.0) 6-9 Months To Reach Production Experimentation cycles delay real deployment.

--- Drafted email (template fallback, no LLM key set) ---

Hi Polly,

I came across Maybe*'s work and this line stopped me: "72% Don't Trust AI
With Live Work AI is tested in isolation, but blocked from real workflows."

I'm Visal, GTM engineer specializing in AI automation. That stat is exactly
the kind of gap I spend my time closing -- turning it from an interesting
insight into something a team can actually act on.

Worth a quick 15-minute conversation to see if there's a fit?

Best,
Visal
```

With `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` set, the last section is
replaced with an LLM-drafted version that weaves the hook in more naturally
instead of quoting it verbatim -- which is how the actual outbound email
referencing Maybe*'s "AI Confidence Crisis" post was produced.

## Notes on this example

- The hook candidates above are real output from the scoring logic in
  `research.py` run against Maybe*'s actual homepage text (fetched
  2026-07-04).
- The tool ranks any sentence containing a percentage/number highest, then
  boosts contrast words ("but", "only", "despite", etc.) since those tend to
  make the strongest one-line hooks.
- The email body itself is deliberately short and templated as a fallback --
  the real value is in the automated research step, not the boilerplate.
