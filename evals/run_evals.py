import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "geniesupport"))
from dotenv import load_dotenv
load_dotenv()

from agent import handle_message
from langchain_groq import ChatGroq
from config import CHAT_MODEL

# --- Hard metric: does it escalate the right things? ---
ESCALATION_TESTS = [
    {"msg": "How do I reset my password?", "expect_escalate": False},
    {"msg": "How do I invite a teammate?", "expect_escalate": False},
    {"msg": "How much is the Pro plan?", "expect_escalate": False},
    {"msg": "I want a refund, this is unacceptable", "expect_escalate": True},
    {"msg": "Please cancel my subscription", "expect_escalate": True},
    {"msg": "What's the capital of France?", "expect_escalate": True},  # out of KB scope
]

def eval_escalation():
    correct = 0
    for t in ESCALATION_TESTS:
        r = handle_message(t["msg"], session_id="eval-esc")
        ok = r["escalated"] == t["expect_escalate"]
        correct += ok
        print(("PASS" if ok else "FAIL"), "|", "escalate" if r["escalated"] else "answer  ",
              "|", t["msg"])
    print(f"\nEscalation accuracy: {correct}/{len(ESCALATION_TESTS)}\n")

# --- Fuzzy metric: LLM-as-judge on answer quality ---
_judge = ChatGroq(model=CHAT_MODEL, temperature=0)   # temp 0 to reduce judge variance
JUDGE_PROMPT = """Score this customer-support answer from 1 to 5 on how helpful, accurate,
and grounded it is. Reply with ONLY a single integer.
Question: {q}
Answer: {a}"""
QUALITY_QUESTIONS = [
    "How do I reset my password?",
    "How do I invite a teammate to my workspace?",
    "What plans does Nimbus offer?",
    "How do I connect Slack?",
]

def eval_quality():
    scores = []
    for q in QUALITY_QUESTIONS:
        r = handle_message(q, session_id="eval-q")
        raw = _judge.invoke(JUDGE_PROMPT.format(q=q, a=r["reply"])).content
        digits = "".join(c for c in raw if c.isdigit())
        score = int(digits[0]) if digits else 0
        scores.append(score)
        print(f"score {score}/5 | {q}")
    if scores:
        print(f"\nAvg answer quality (LLM-judge): {sum(scores)/len(scores):.1f}/5")

if __name__ == "__main__":
    print("== Escalation accuracy ==")
    eval_escalation()
    print("== Answer quality (LLM-as-judge) ==")
    eval_quality()