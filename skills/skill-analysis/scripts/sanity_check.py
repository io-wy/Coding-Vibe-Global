"""Phase 6 SDK sanity check.

Verifies that the simulated `available_skills` system prompt + `<skill_call>`
token detection actually correlate with intent. Required before relying on
Phase 6 eval numbers (per references/empirical-verification.md §7 disclaimer).

Picks a fictional but unambiguous skill, then runs N trials each on:
  - an obvious-trigger query (should approach trigger_rate = 1.0)
  - an obvious-non-trigger query (should approach trigger_rate = 0.0)

If the gap collapses, the SYSTEM_PROMPT_TEMPLATE in run_eval.py needs tuning
before any real Phase 6 run is meaningful.

Cost: ~$0.012 per call × 2 queries × N trials. Default 5 → ~$0.12 per run.

Usage:
    python -m scripts.sanity_check [--trials 5] [--model claude-sonnet-4-6]
"""

from __future__ import annotations

import argparse
import sys

from .run_eval import build_system_prompt, run_single_query
from .utils import make_client


SANITY_SKILL_NAME = "logging-helper"
SANITY_DESCRIPTION = (
    "Use when the user wants to add structured logging, set up a log "
    "aggregator, or improve observability of a backend service. Triggers on "
    "phrases like 'add logs', 'log every request', 'set up structured "
    "logging', 'send logs to Loki/ELK/Datadog'."
)
OBVIOUS_TRIGGER_QUERY = "Add structured logging to my Go HTTP handler"
OBVIOUS_NON_TRIGGER_QUERY = "What's the time complexity of quicksort?"


def run_trials(client, system_prompt, query, skill_name, trials):
    fired = 0
    for _ in range(trials):
        ok = run_single_query(client, system_prompt, query, skill_name)
        sys.stderr.write("X" if ok else ".")
        sys.stderr.flush()
        if ok:
            fired += 1
    sys.stderr.write("\n")
    return fired


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 6 SDK sanity check.")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--model", type=str, default="claude-sonnet-4-6")
    args = parser.parse_args()

    client = make_client()
    sp = build_system_prompt(SANITY_SKILL_NAME, SANITY_DESCRIPTION)

    print(f"\nObvious-trigger query: {OBVIOUS_TRIGGER_QUERY!r}")
    pos_fired = run_trials(client, sp, OBVIOUS_TRIGGER_QUERY,
                           SANITY_SKILL_NAME, args.trials)
    pos_rate = pos_fired / args.trials
    print(f"  trigger_rate = {pos_rate:.2f} ({pos_fired}/{args.trials})")

    print(f"\nObvious-non-trigger query: {OBVIOUS_NON_TRIGGER_QUERY!r}")
    neg_fired = run_trials(client, sp, OBVIOUS_NON_TRIGGER_QUERY,
                           SANITY_SKILL_NAME, args.trials)
    neg_rate = neg_fired / args.trials
    print(f"  trigger_rate = {neg_rate:.2f} ({neg_fired}/{args.trials})")

    print("\n--- Diagnosis ---")
    ok = pos_rate >= 0.8 and neg_rate <= 0.2
    if ok:
        print("OK SDK trigger detection works as expected.")
        return 0
    if pos_rate < 0.8:
        print(f"FAIL Obvious-trigger fires only {pos_rate:.0%} — under-triggers.")
    if neg_rate > 0.2:
        print(f"FAIL Obvious-non-trigger fires {neg_rate:.0%} — over-triggers.")
    print("Tune SYSTEM_PROMPT_TEMPLATE in scripts/run_eval.py before "
          "relying on results.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
