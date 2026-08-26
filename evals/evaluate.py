"""Run the golden dataset, score it, and compare to the saved baseline.
Exits with an error code if quality dropped — which lets CI block bad changes (Layer 4).
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from src.geniesupport.agent import handle_message

HERE = os.path.dirname(__file__)
GOLDEN = os.path.join(HERE, "golden_dataset.json")
BASELINE = os.path.join(HERE, "baseline.json")


def run_scores():
    data = json.load(open(GOLDEN, encoding="utf-8"))
    esc_correct = 0
    src_correct = 0
    src_total = 0

    for case in data:
        r = handle_message(case["question"], session_id="eval")

        # escalation metric — every case has a definite right answer
        if r["escalated"] == case["should_escalate"]:
            esc_correct += 1

        # retrieval metric — only for cases we expect it to answer
        if case["expect_source"]:
            src_total += 1
            titles = [s["title"] for s in r["sources"]]
            if case["expect_source"] in titles:
                src_correct += 1

    return {
        "escalation_accuracy": round(esc_correct / len(data), 3),
        "retrieval_accuracy": round(src_correct / src_total, 3) if src_total else 0.0,
    }


def main():
    scores = run_scores()
    print("Scores:", scores)

    if os.path.exists(BASELINE):
        baseline = json.load(open(BASELINE))
        regressed = False
        for metric, value in scores.items():
            old = baseline.get(metric, 0)
            if value < old - 0.01:              # small tolerance for noise
                print(f"  REGRESSION: {metric} dropped {old} -> {value}")
                regressed = True
            else:
                print(f"  OK: {metric} {old} -> {value}")
        if regressed:
            sys.exit(1)                          # fail — this is the CI gate for Layer 4
    else:
        print("No baseline yet. Saving current scores as baseline.")

    json.dump(scores, open(BASELINE, "w"), indent=2)


if __name__ == "__main__":
    main()