import time
from langchain_groq import ChatGroq
from src.geniesupport.config import CHAT_MODEL, RELEVANCE_THRESHOLD
from geniesupport.intent import classify_intent
from src.geniesupport.retrieval import retrieve_with_scores
from src.geniesupport.memory import add_turn, format_history
from src.geniesupport.cost import extract_usage, compute_cost

_llm = ChatGroq(model=CHAT_MODEL, temperature=0)

ANSWER_SYSTEM = """You are a friendly, concise support assistant for Nimbus, a project
management SaaS. Answer using ONLY the help-doc context below. Cite the doc titles you used
in square brackets, e.g. [Billing]. If the context doesn't fully answer the question, say
you're not fully certain and that you'll connect them with a human. Never invent features.

Conversation so far:
{history}

Help-doc context:
{context}"""

ESCALATION_MESSAGE = ("I want to make sure you get the right help here, so I'm connecting "
                      "you with a member of our support team who'll follow up shortly.")

def _format_context(scored_docs):
    return "\n\n---\n\n".join(
        f"[{d.metadata.get('title', 'Doc')}]\n{d.page_content}" for d, _ in scored_docs
    )

def handle_message(message: str, session_id: str = "default") -> dict:
    t0 = time.time()
    history = format_history(session_id)        # prior turns only
    sources, cost, escalated, reason = [], 0.0, False, None

    # 1. Intent
    intent = classify_intent(message)

    if intent == "human_request":
        # 2a. Some intents always go to a human
        reply = ESCALATION_MESSAGE
        escalated, reason = True, "sensitive intent (complaint / refund / cancellation)"
    elif intent == "chitchat":
        reply = "Hi! I'm the Nimbus support assistant. How can I help you today?"
    else:
        # 2b. Retrieve with confidence scores
        scored = retrieve_with_scores(message)
        top_score = scored[0][1] if scored else 0.0

        if not scored or top_score < RELEVANCE_THRESHOLD:
            # 3. Confidence gate failed → escalate
            reply = ESCALATION_MESSAGE
            escalated = True
            reason = f"low retrieval confidence (top score {top_score:.2f} < {RELEVANCE_THRESHOLD})"
        else:
            # 4. Confident → generate a grounded answer
            context = _format_context(scored)
            prompt = ANSWER_SYSTEM.format(history=history, context=context)
            response = _llm.invoke([("system", prompt), ("human", message)])
            reply = response.content
            pt, ct = extract_usage(response)
            cost = compute_cost(pt, ct)
            sources = [{"title": d.metadata.get("title", "Doc"),
                        "snippet": d.page_content[:160]} for d, _ in scored]

    # record the exchange in memory
    add_turn(session_id, "customer", message)
    add_turn(session_id, "assistant", reply)

    return {
        "reply": reply,
        "escalated": escalated,
        "reason": reason,
        "sources": sources,
        "latency_ms": round((time.time() - t0) * 1000),
        "cost_usd": round(cost, 6),
    }