"""Phase 6 sub-phase 6c: run skill description trigger evaluation.

Measures actual trigger behaviour by streaming Claude responses and scanning for
the simulated `<skill_call name="..." />` marker. Uses threading + queue.Queue
to read the SDK stream so timeouts work on Windows (where select.select on pipes
is unsupported).

Usage:
    python -m scripts.run_eval <skill_dir> <eval_set.json> --out <results.json>
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import anthropic

from .utils import make_client, parse_skill_md


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_RUNS_PER_QUERY = 3
DEFAULT_TRIGGER_THRESHOLD = 0.5
DEFAULT_TIMEOUT_SEC = 30.0
DEFAULT_MAX_TOKENS = 1024
DEFAULT_COST_PER_CALL = 0.012  # rough Sonnet 4.6 estimate (input ~1.5k + output ~0.3k)

SYSTEM_PROMPT_TEMPLATE = """You have access to the following skill:

- {skill_name}: {description}

If the user's request matches the skill's description, invoke it by outputting exactly this token (and nothing else surrounding it on that line):
<skill_call name="{skill_name}" />

Then continue responding normally. If no skill matches, just respond normally without the skill_call tag.
"""


def build_system_prompt(skill_name: str, description: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        skill_name=skill_name, description=description
    )


def check_trigger(accumulated_text: str, skill_name: str) -> bool:
    """Return True if the accumulated streamed text invokes the target skill."""
    needle = f'<skill_call name="{skill_name}"'
    return needle in accumulated_text


def _stream_reader(stream, q: queue.Queue) -> None:
    """Background thread: pump text chunks from SDK stream into queue."""
    try:
        for text in stream.text_stream:
            if text:
                q.put(("text", text))
        q.put(("done", None))
    except Exception as e:  # noqa: BLE001 — surface upstream
        q.put(("error", e))


def run_single_query(
    client: anthropic.Anthropic,
    system_prompt: str,
    query: str,
    skill_name: str,
    *,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> bool:
    """Run one query, return True if the skill_call marker was emitted.

    Threading + queue.Queue avoids select.select on pipes (Windows-incompatible).
    The reader thread is daemon so it dies with the process if we early-break.
    """
    accumulated: list[str] = []
    triggered = False

    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": query}],
    ) as stream:
        q: queue.Queue = queue.Queue()
        t = threading.Thread(target=_stream_reader, args=(stream, q), daemon=True)
        t.start()

        deadline = time.time() + timeout
        while time.time() < deadline and not triggered:
            try:
                kind, payload = q.get(timeout=0.5)
            except queue.Empty:
                continue
            if kind == "done":
                break
            if kind == "error":
                raise payload
            accumulated.append(payload)
            if check_trigger("".join(accumulated), skill_name):
                triggered = True
                break

    return triggered


def evaluate_query(
    client: anthropic.Anthropic,
    system_prompt: str,
    query: str,
    should_trigger: bool,
    skill_name: str,
    *,
    runs: int = DEFAULT_RUNS_PER_QUERY,
    threshold: float = DEFAULT_TRIGGER_THRESHOLD,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT_SEC,
) -> dict:
    """Evaluate one query with multi-vote, return result record."""
    triggers = 0
    for _ in range(runs):
        if run_single_query(
            client, system_prompt, query, skill_name,
            model=model, timeout=timeout,
        ):
            triggers += 1
    rate = triggers / runs if runs > 0 else 0.0
    fired = rate >= threshold
    passed = fired == should_trigger
    return {
        "query": query,
        "should_trigger": should_trigger,
        "trigger_rate": rate,
        "triggers": triggers,
        "runs": runs,
        "fired": fired,
        "pass": passed,
    }


def run_eval(
    skill_dir: Path,
    eval_set: list[dict],
    *,
    runs: int = DEFAULT_RUNS_PER_QUERY,
    threshold: float = DEFAULT_TRIGGER_THRESHOLD,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    iteration: int = 0,
    description_override: Optional[str] = None,
) -> dict:
    """Run a full eval (all queries × runs) on a skill.

    Pass `description_override` to evaluate a candidate description without
    editing SKILL.md (used by run_loop during 6d iterations).
    """
    name, description, _ = parse_skill_md(skill_dir)
    if description_override is not None:
        description = description_override
    if not name or not description:
        raise ValueError(f"SKILL.md at {skill_dir} missing name or description")

    system_prompt = build_system_prompt(name, description)
    client = make_client()

    results: list[dict] = []
    for i, item in enumerate(eval_set, start=1):
        q_text = item["query"]
        should = bool(item["should_trigger"])
        sign = "+" if should else "-"
        print(
            f"  [{i}/{len(eval_set)}] {sign} {q_text[:60]}",
            file=sys.stderr,
        )
        result = evaluate_query(
            client, system_prompt, q_text, should, name,
            runs=runs, threshold=threshold,
            model=model, timeout=timeout,
        )
        result["category"] = item.get("category", "")
        results.append(result)

    passed = sum(1 for r in results if r["pass"])
    return {
        "skill_name": name,
        "description": description,
        "iteration": iteration,
        "results": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
        },
    }


def estimate_cost(
    eval_set: list[dict],
    runs: int,
    iterations: int,
    cost_per_call: float = DEFAULT_COST_PER_CALL,
) -> float:
    return len(eval_set) * runs * iterations * cost_per_call


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run skill description trigger evaluation (Phase 6 6c)."
    )
    parser.add_argument("skill_dir", type=Path, help="Path to skill directory")
    parser.add_argument("eval_set", type=Path, help="Path to eval_set.json")
    parser.add_argument("--out", type=Path, default=None,
                        help="Write results JSON here (default: stdout)")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS_PER_QUERY)
    parser.add_argument("--threshold", type=float, default=DEFAULT_TRIGGER_THRESHOLD)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--iteration", type=int, default=0)
    parser.add_argument("--cost-cap", type=float, default=5.0,
                        help="Refuse to run if estimated cost exceeds this (USD)")
    parser.add_argument("--yes", action="store_true",
                        help="Skip cost confirmation prompt")
    args = parser.parse_args()

    eval_set = json.loads(args.eval_set.read_text(encoding="utf-8"))
    if not isinstance(eval_set, list):
        print("eval_set must be a JSON array", file=sys.stderr)
        return 1

    estimated = estimate_cost(eval_set, args.runs, 1)
    print(
        f"Estimated cost: ~${estimated:.2f} "
        f"({len(eval_set)} queries × {args.runs} runs × ${DEFAULT_COST_PER_CALL})",
        file=sys.stderr,
    )
    if estimated > args.cost_cap and not args.yes:
        print(
            f"Cost ${estimated:.2f} exceeds cap ${args.cost_cap}. "
            f"Pass --yes to proceed.",
            file=sys.stderr,
        )
        return 2

    out = run_eval(
        args.skill_dir, eval_set,
        runs=args.runs, threshold=args.threshold,
        model=args.model, timeout=args.timeout,
        iteration=args.iteration,
    )

    payload = json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(f"Results written to {args.out}", file=sys.stderr)
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    sys.exit(main())
