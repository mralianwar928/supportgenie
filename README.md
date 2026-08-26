# SupportGenie — AI Customer Support Agent

An AI support agent that answers customer questions from a company's help docs, cites its
sources, and **escalates to a human when it's unsure or the request is sensitive** — instead
of guessing. Tracks the latency and cost of every interaction.

The point isn't that it answers questions. It's that it *knows when not to*.

<!-- Add a GIF here of it answering a question, then escalating an out-of-scope one — that
     side-by-side is the whole value proposition. -->
<!-- ![demo](docs/demo.gif) -->

## What it does

Every incoming message is classified and routed:

- **A question it can answer** → retrieves the relevant help docs and replies with citations
- **A sensitive request** (refund, cancellation, complaint) → escalates to a human immediately
- **Something outside the help docs** → escalates, rather than hallucinating an answer
- **Chit-chat** → a friendly reply, no retrieval

It decides whether it *actually knows* the answer by measuring retrieval confidence — if the
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

Along the way it keeps short per-session conversation memory (so follow-up questions have
context) and records the token cost and latency of each request.

**Stack:** Python · FastAPI · LangChain · Groq (`openai/gpt-oss-20b`) · sentence-transformers (local embeddings) · ChromaDB

## Run it

Needs Python 3.11.

```bash
python -m venv .venv && .venv\Scripts\activate     # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
# add GROQ_API_KEY to a .env file (free key at console.groq.com)

python -m src.supportgenie.ingest       # build the knowledge base from data/help_docs/
python -m src.supportgenie.cli          # test in the terminal
# or run the API:
uvicorn main:app --app-dir src/supportgenie --reload   # http://localhost:8000/docs
```

Try `How much is the Pro plan?` (answers, cites Billing), then `I want a refund` (escalates),
then `What's the weather in Paris?` (escalates — not in the docs).

## Results

Two metrics — one hard, one judged (`python evals/run_evals.py`):

| Metric | Result |
|---|---|
| Escalation accuracy (routes the right things to a human) | 6/6 |
| Answer quality — LLM-as-judge, 1–5 | 4.8/5 |

## Design notes

- **Confidence-based escalation.** The decision to hand off is grounded in the retrieval
  relevance score, calibrated against real data — not the model's self-assessment, which is
  unreliable. This is what stops it hallucinating on out-of-scope questions.
- **Two escalation triggers.** Sensitive intents (refunds, complaints) are caught by the
  intent router *before* retrieval; unknown topics are caught by the confidence gate. Some
  requests a bot should never handle, regardless of what it can find.
- **Cost tracking.** Every response's token usage is priced and logged, so the running cost
  of the service is visible per request — production economics, not just "does it work."
- **Answer quality via LLM-as-judge**, at temperature 0 with a fixed rubric to limit judge
  variance, paired with a hard escalation metric that has a definite right answer.

The knowledge base here is a fictional SaaS ("Nimbus") — swap `data/help_docs/` for any set
of documents and it works unchanged.
