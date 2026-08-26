# Architecture

SupportGenie is an AI customer support agent with a full production operations layer. It
answers customer questions from a knowledge base, cites its sources, and escalates to a
human when it is unsure or the request is sensitive and it is observable, evaluated,
cost-controlled, and gated by CI.

## Request flow

```
message
  → intent classification (question / chitchat / human_request / unclear)
      ├─ human_request → escalate (a human must own refunds, complaints, cancellations)
      ├─ chitchat      → friendly canned reply (no retrieval, no cost)
      └─ question → retrieve top-k help-doc chunks (with relevance scores)
                       ├─ top score < threshold → escalate (knowledge base can't answer)
                       └─ top score ≥ threshold → grounded answer + citations
  → record conversation memory, track latency + token cost, log + trace
```

## Components

| Component | Responsibility |
|---|---|
| `intent.py` | Classifies each message so it can be routed (structured output, JSON mode) |
| `retrieval.py` | Returns top-k chunks **with relevance scores** — the score drives escalation |
| `agent.py` | Orchestrates the whole decision flow; single source of truth for the logic |
| `memory.py` | Bounded per-session conversation history for multi-turn context |
| `cost.py` | Extracts token usage from each response and prices it |
| `cache.py` | Reuses answers for repeated questions (cost control) |
| `ratelimit.py` | Caps requests per session (abuse / runaway-cost protection) |
| `main.py` | FastAPI service exposing `/chat` and `/health` |
| `evals/` | Golden-dataset evaluation with regression detection |

## Key decisions (and why)

- **Escalation gates on the retrieval relevance score, not the model's self-assessment.**
  LLMs are unreliable at knowing what they don't know and they hallucinate confidently. A
  measurable retrieval score is a dependable signal: below a calibrated threshold means the
  knowledge base doesn't cover the question, so the agent hands off to a human.

- **Two independent escalation triggers.** Sensitive intents (refunds, complaints,
  cancellations) are caught by the intent router before retrieval,some requests a bot
  should never answer regardless of what it can find. Unknown topics are caught by the
  confidence gate. Separating these keeps each concern clear.

- **Answers are cached; escalations are not.** Repeated questions ("how do I reset my
  password?") are served from cache for free, cutting cost dramatically at scale.
  Escalations always route fresh, because an escalation is a state, not an answer to reuse.

- **Evaluation is a CI gate, not a manual step.** A golden dataset scores every change with
  regression detection; if escalation or retrieval accuracy drops past a tolerance, the
  build fails and the change is blocked. Quality can't silently degrade.

- **Observability is built in.** Every request is traced (LangSmith) with per-step latency
  and token cost, so failures can be diagnosed from the trace instead of guessed at.

## Trade-offs and what I'd change at scale

- **Memory and cache are in-memory** (per process). For a multi-instance deployment I'd move
  both to Redis so they're shared and survive restarts.
- **Rate limiting is in-memory per session.** At scale I'd use a distributed limiter
  (e.g. Redis-backed) so limits hold across instances.
- **The relevance threshold is a single global value.** With more traffic I'd calibrate it
  per intent or per document type, and monitor it against live escalation rates.
- **Caching is exact-match.** Semantic caching (reusing answers for *similar* questions via
  embeddings) would raise the hit rate; it's designed but kept simple here.
- **Model routing.** At higher volume I'd route easy questions to a cheaper model and reserve
  the larger model for hard ones, to cut cost further.

## Stack

Python · FastAPI · LangChain · Groq · sentence-transformers (local embeddings) · ChromaDB ·
LangSmith (tracing) · GitHub Actions (CI quality gate) · Docker