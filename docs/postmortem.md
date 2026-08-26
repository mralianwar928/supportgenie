# Postmortem: false escalations after a threshold change

## Summary
A change to the retrieval-confidence threshold caused SupportGenie to wrongly escalate
questions it should have answered. The regression was caught by the evaluation pipeline
before it could reach production.

## Impact
In the affected configuration, real, answerable questions (e.g. "How much is the Pro
plan?") were routed to a human instead of being answered. Escalation accuracy dropped from
1.0 to 0.375 and retrieval accuracy from 1.0 to 0.0 on the golden dataset effectively,
the agent stopped answering anything.

## Timeline
- The escalation confidence threshold (`RELEVANCE_THRESHOLD`) was set too high.
- The golden-dataset evaluation was run.
- The evaluator detected a regression against the saved baseline and failed
  (`escalation_accuracy 1.0 -> 0.375`, `retrieval_accuracy 1.0 -> 0.0`), exiting with an
  error before the change could be shipped.

## How it was detected
The evaluation pipeline compares every run against a saved baseline and flags any metric
that drops past a tolerance. It caught the regression immediately. LangSmith traces
confirmed the cause: retrieval was returning the correct documents, but their relevance
scores were below the raised threshold, so the confidence gate fired incorrectly.

## Root cause
The relevance scores produced by the embedding and distance setup do not sit on a simple
0–1 scale ,genuine matches scored around 0.16 while clearly-irrelevant content scored
around -0.4. The threshold had been set for a different, assumed scale, so it no longer sat
in the gap between "relevant" and "irrelevant" and rejected valid matches.

## Fix
The threshold was recalibrated against observed scores set below real matches (~0.16) and
above irrelevant content (~-0.4). The evaluation suite confirmed escalation and retrieval
accuracy returned to 1.0.

## Prevention
- The golden-dataset regression test now runs in CI on every push, so this class of change
  is blocked automatically before merge.
- The threshold is documented as a value that must be calibrated against real retrieval
  scores, not assumed to be on a 0–1 scale.

## Lessons
- Confidence thresholds must be calibrated empirically against real score distributions, not
  set by intuition.
- Automated evaluation with regression detection is what turned a silent, severe quality
  failure into an immediate, visible, blocked build.