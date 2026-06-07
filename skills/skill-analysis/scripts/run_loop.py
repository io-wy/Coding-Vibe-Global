"""Phase 6 orchestrator: stratified split + baseline + iterate + best-by-test.

Implements sub-phases 6b–6d end-to-end. Defenses against overfitting:
  - Stratified split on should_trigger, fixed seed (reproducible).
  - improve_description sees only train_results + blinded history.
  - Best iteration selected by test_passed (not train_passed).

Usage:
    python -m scripts.run_loop <skill_dir> <eval_set.json> --out-dir <dir>

Output files (under --out-dir):
  baseline_results.json  — iteration 1 full results
  iter_<N>_results.json  — per-iteration full results
  history.json           — iteration log + train/test set + best pointer
  best_description.txt   — winning description text
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from .improve_description import improve_description
from .run_eval import DEFAULT_MODEL, estimate_cost, run_eval
from .utils import parse_skill_md


DEFAULT_HOLDOUT = 0.4
DEFAULT_SEED = 42
DEFAULT_MAX_ITERATIONS = 5
DEFAULT_RUNS = 3


def stratified_split(
    eval_set: list[dict],
    holdout: float = DEFAULT_HOLDOUT,
    seed: int = DEFAULT_SEED,
) -> tuple[list[dict], list[dict]]:
    """Split into train/test, balanced across should_trigger=true/false."""
    pos = [e for e in eval_set if e["should_trigger"]]
    neg = [e for e in eval_set if not e["should_trigger"]]
    rng = random.Random(seed)
    rng.shuffle(pos)
    rng.shuffle(neg)
    n_pos_test = max(1, int(len(pos) * holdout))
    n_neg_test = max(1, int(len(neg) * holdout))
    test = pos[:n_pos_test] + neg[:n_neg_test]
    train = pos[n_pos_test:] + neg[n_neg_test:]
    return train, test


def split_results_by_set(
    full_results: dict,
    train_set: list[dict],
    test_set: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Partition the eval results back into train and test buckets by query."""
    train_queries = {e["query"] for e in train_set}
    test_queries = {e["query"] for e in test_set}
    train_results = [r for r in full_results["results"] if r["query"] in train_queries]
    test_results = [r for r in full_results["results"] if r["query"] in test_queries]
    return train_results, test_results


def _count_pass(results: list[dict]) -> tuple[int, int]:
    passed = sum(1 for r in results if r["pass"])
    return passed, len(results) - passed


def run_loop(
    skill_dir: Path,
    eval_set: list[dict],
    out_dir: Path,
    *,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    runs: int = DEFAULT_RUNS,
    holdout: float = DEFAULT_HOLDOUT,
    seed: int = DEFAULT_SEED,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Full Phase 6 loop. Returns the summary dict (also written to history.json)."""
    out_dir.mkdir(parents=True, exist_ok=True)

    train_set, test_set = stratified_split(eval_set, holdout, seed)
    train_pos = sum(e["should_trigger"] for e in train_set)
    test_pos = sum(e["should_trigger"] for e in test_set)
    print(
        f"Split: train={len(train_set)} (pos={train_pos}) "
        f"test={len(test_set)} (pos={test_pos})",
        file=sys.stderr,
    )

    name, current_desc, _ = parse_skill_md(skill_dir)
    if not name or not current_desc:
        raise ValueError(f"SKILL.md at {skill_dir} missing name or description")

    history: list[dict] = []
    stopped_early = False

    for iteration in range(1, max_iterations + 1):
        print(f"\n=== Iteration {iteration}/{max_iterations} ===", file=sys.stderr)

        full = run_eval(
            skill_dir, eval_set,
            runs=runs, model=model,
            iteration=iteration,
            description_override=current_desc,
        )
        train_results, test_results = split_results_by_set(full, train_set, test_set)
        train_passed, train_failed = _count_pass(train_results)
        test_passed, test_failed = _count_pass(test_results)

        record = {
            "iter": iteration,
            "description": current_desc,
            "train_passed": train_passed,
            "train_failed": train_failed,
            "test_passed": test_passed,
            "test_failed": test_failed,
            "results": full["results"],
        }
        history.append(record)

        iter_path = out_dir / f"iter_{iteration}_results.json"
        iter_path.write_text(
            json.dumps(full, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if iteration == 1:
            (out_dir / "baseline_results.json").write_text(
                json.dumps(full, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        print(
            f"  train: {train_passed}/{len(train_results)} | "
            f"test: {test_passed}/{len(test_results)}",
            file=sys.stderr,
        )

        if train_failed == 0:
            print("  All train queries pass — stopping early.", file=sys.stderr)
            stopped_early = True
            break
        if iteration == max_iterations:
            break

        # Blinded improvement: only train_results + history-without-test-fields
        blinded_history = [
            {
                "iter": h["iter"],
                "description": h["description"],
                "train_passed": h["train_passed"],
                "train_failed": h["train_failed"],
            }
            for h in history
        ]
        try:
            new_desc = improve_description(
                skill_dir, train_results, blinded_history,
                model=model,
                description_override=current_desc,
            )
        except ValueError as e:
            print(
                f"  improve_description failed: {e}\n"
                f"  Stopping loop and selecting best from prior iterations.",
                file=sys.stderr,
            )
            break
        print(f"  Generated new description ({len(new_desc)} chars)", file=sys.stderr)
        current_desc = new_desc

    # Pick best by test_passed (anti-overfit), tie-break by train_passed.
    if test_set:
        best = max(history, key=lambda h: (h["test_passed"], h["train_passed"]))
    else:
        best = max(history, key=lambda h: h["train_passed"])

    summary = {
        "skill_name": name,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "max_iterations": max_iterations,
        "runs_per_query": runs,
        "holdout": holdout,
        "seed": seed,
        "stopped_early": stopped_early,
        "best_iteration": best["iter"],
        "best_description": best["description"],
        "best_train_passed": best["train_passed"],
        "best_train_failed": best["train_failed"],
        "best_test_passed": best["test_passed"],
        "best_test_failed": best["test_failed"],
        "iterations": history,
        "train_set": train_set,
        "test_set": test_set,
    }

    (out_dir / "history.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "best_description.txt").write_text(
        best["description"], encoding="utf-8"
    )

    print(
        f"\nBest iteration: #{best['iter']}  "
        f"train {best['train_passed']}/{best['train_passed']+best['train_failed']}  "
        f"test {best['test_passed']}/{best['test_passed']+best['test_failed']}",
        file=sys.stderr,
    )
    print(f"Wrote {out_dir}/best_description.txt and history.json", file=sys.stderr)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 6 full loop (split + baseline + iterate + select)."
    )
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("eval_set", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--holdout", type=float, default=DEFAULT_HOLDOUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--cost-cap", type=float, default=5.0)
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    eval_set = json.loads(args.eval_set.read_text(encoding="utf-8"))
    if not isinstance(eval_set, list):
        print("eval_set must be a JSON array", file=sys.stderr)
        return 1

    estimated = estimate_cost(eval_set, args.runs, args.max_iterations)
    print(
        f"Estimated max cost (worst case all iterations run): "
        f"~${estimated:.2f}",
        file=sys.stderr,
    )
    if estimated > args.cost_cap and not args.yes:
        print(
            f"Cost ${estimated:.2f} exceeds cap ${args.cost_cap}. "
            f"Pass --yes to proceed.",
            file=sys.stderr,
        )
        return 2

    run_loop(
        args.skill_dir, eval_set, args.out_dir,
        max_iterations=args.max_iterations,
        runs=args.runs,
        holdout=args.holdout,
        seed=args.seed,
        model=args.model,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
