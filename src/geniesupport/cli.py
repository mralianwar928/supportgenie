# cli.py  (for local testing)
from dotenv import load_dotenv
load_dotenv()
from src.geniesupport.agent import handle_message

print("SupportGenie CLI — type a customer message. Ctrl+C to exit.\n")
while True:
    try:
        msg = input("Customer: ").strip()
        if not msg:
            continue
        r = handle_message(msg, session_id="cli")
        tag = " [ESCALATED]" if r["escalated"] else ""
        print(f"\nSupportGenie{tag}: {r['reply']}")
        if r["reason"]:
            print(f"  reason: {r['reason']}")
        if r["sources"]:
            print(f"  sources: {', '.join(s['title'] for s in r['sources'])}")
        print(f"  latency: {r['latency_ms']}ms · cost: ${r['cost_usd']:.6f}\n")
    except KeyboardInterrupt:
        print("\nGoodbye!")
        break