# SupportGenie — Production-Operated AI Support Agent

An AI customer support agent that answers questions from a company's help docs, cites its
sources, and escalates to a human when it's unsure or the request is sensitive and wrapped
in a full production operations layer: tracing, automated evaluation with a CI quality gate,
cost controls, and documented incident response.

The point isn't just that it answers questions. It's that it *knows when not to*, and that
it can be **run and maintained in production**

<!-- Add a GIF: answer a question (with citation), then escalate an out-of-scope one. That
     side-by-side is the whole value proposition. -->
<!-- ![demo](docs/demo.gif) -->

## What it does

Every incoming message is classified and routed:

- **A question it can answer** → retrieves the relevant help docs and replies with citations
- **A sensitive request** (refund, cancellation, complaint) → escalates to a human immediately
- **Something outside the help docs** → escalates instead of hallucinating an answer
- **Chit-chat** → a friendly reply, no retrieval

It decides whether it *actually knows* the answer by measuring retrieval confidence.if the
best-matching document scores below a calibrated threshold, it hands off to a human.

## How it works

```
message → classify intent → route
                              ├─ sensitive request ─────────▶ escalate to human
                              ├─ chit-chat ─────────────────▶ friendly reply
                              └─ question → retrieve (with confidence score)
                                              ├─ score < threshold ─▶ escalate to human
                                              └─ score ≥ threshold ─▶ grounded answer + citations
```

Per-session memory gives multi-turn context; every request's latency and token cost are
tracked and logged.

## Production operations layer

This is what makes it a system you can run, not just a demo:

- **Observability (LangSmith)** — every request is traced end to end: intent, retrieval,
  generation, with per-step latency and token cost. Failures are diagnosed from the trace,
  not guessed at.
- **Evaluation pipeline** — a golden dataset scored on every change, with regression
  detection against a saved baseline.
- **CI quality gate (GitHub Actions)** — every push runs the evals; if escalation or
  retrieval accuracy regresses past a tolerance, the build fails and the change is blocked.
  Quality can't silently degrade.
- **Cost control** — response caching (repeated questions are served for free) and
  per-session rate limiting (abuse / runaway-cost protection).
- **Documented operations** — an [architecture doc](docs/ARCHITECTURE.md) explaining the
  design decisions, and a real [incident postmortem](docs/POSTMORTEM.md) of a
  threshold-regression caught by the eval pipeline.

**Stack:** Python · FastAPI · LangChain · Groq · sentence-transformers (local embeddings) ·
ChromaDB · LangSmith · GitHub Actions · Docker

## Results

Golden-dataset evaluation (`python evals/evaluate.py`):

| Metric | Result |
|---|---|
| Escalation accuracy (routes the right things to a human) | 1.0 |
| Retrieval accuracy (answers cite the correct help doc) | 1.0 |

The eval pipeline also detects regressions: a deliberately mis-calibrated threshold dropped
escalation accuracy to 0.375 and retrieval to 0.0, which the pipeline caught and the CI gate
would block (see the [postmortem](docs/POSTMORTEM.md)).

## Run it

Needs Python 3.11.

```bash
python -m venv .venv && .venv\Scripts\activate     # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
# add GROQ_API_KEY to a .env file (free key at console.groq.com)
# optional: LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT for tracing

python -m src.geniesupport.ingest       # build the knowledge base from data/help_docs/
python -m src.geniesupport.cli          # test in the terminal
# or run the API:
uvicorn src.geniesupport.main:app --reload    # http://localhost:8000/docs
```

Try `How much is the Pro plan?` (answers, cites Billing), then `I want a refund` (escalates),
then `What's the weather in Paris?` (escalates — not in the docs).

## Design notes

- **Confidence-based escalation.** The decision to hand off is grounded in the retrieval
  relevance score, calibrated against real data not the model's self-assessment, which is
  unreliable.
- **Two escalation triggers.** Sensitive intents are caught by the router *before* retrieval;
  unknown topics are caught by the confidence gate.
- **Eval-as-a-gate.** Evaluation runs in CI, so no change ships unless it passes the quality
  bar. This is what lets the system evolve safely.

The knowledge base is a fictional SaaS ("Nimbus") — swap `data/help_docs/` for any set of
documents and it works unchanged.