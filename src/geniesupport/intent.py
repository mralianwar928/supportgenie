from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from src.geniesupport.config import CHAT_MODEL

class Intent(BaseModel):
    category: str = Field(description="question | chitchat | human_request | unclear")

_llm = ChatGroq(model=CHAT_MODEL, temperature=0)
_intent_llm = _llm.with_structured_output(Intent, method="json_mode")

PROMPT = """Classify the customer's message into exactly one category.
Respond in JSON with a single key "category".
- "question": a support question answerable from help documentation
- "chitchat": greetings, thanks, small talk
- "human_request": complaints, refunds, cancellations, billing disputes, legal, or asking for a human
- "unclear": too vague to tell

Message: {message}"""

def classify_intent(message: str) -> str:
    try:
        return _intent_llm.invoke(PROMPT.format(message=message)).category
    except Exception:
        return "unclear"   # fail safe: if classification breaks, treat as unclear