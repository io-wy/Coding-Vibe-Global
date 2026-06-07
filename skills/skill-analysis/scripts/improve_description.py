"""Phase 6 sub-phase 6d: rewrite a skill description from training failures.

CRITICAL: this is the BLINDED step. Receives only train_results + iteration
history with test_* fields stripped. Never sees test queries or test scores.

Usage:
    python -m scripts.improve_description <skill_dir> <train_results.json> \\
        [--history history.json] [--out new_desc.txt]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import anthropic

from .utils import make_client, parse_skill_md


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 2048
MAX_DESCRIPTION_CHARS = 1024


PROMPT_TEMPLATE = """You are tuning the trigger description of a Claude Code skill.

Skill name: {skill_name}

Current description (between the dashes):
---
{description}
---

The description acts as a router: it decides whether Claude invokes this skill for a given user request. We measured how the current description behaves on training queries, each run multiple times. trigger_rate is the fraction of runs where the skill fired.

TRAINING RESULTS:
{train_block}

ITERATION HISTORY (prior attempts at improving this description):
{history_block}

YOUR TASK: rewrite the description so:
1. should_trigger=true queries that currently FAIL start triggering (fix recall).
2. should_trigger=false queries that currently FIRE stop firing (fix precision).
3. Preserve trigger phrases that already work — do not regress passing queries.
4. Keep the description focused on WHEN to invoke, not WHAT the skill does internally.

HARD CONSTRAINTS:
- Maximum {max_chars} characters.
- No angle brackets (< or >). They break YAML frontmatter.
- No markdown code fences. No quotes wrapping the whole thing.

OUTPUT: respond with ONLY the new description text, nothing else. No preamble, no explanation, no labels, no quote marks.
"""


def format_results_block(results: list[dict]) -> str:
    """Render train results as a compact bullet list for the prompt."""
    if not results:
        return "(no training queries)"
    lines = []
    for r in results:
        sign = "+" if r["should_trigger"] else "-"
        outcome = "PASS" if r["pass"] else "FAIL"
        rate = r["trigger_rate"]
        q_text = r["query"]
        cat = r.get("category", "")
        cat_tag = f"[{cat}] " if cat else ""
        lines.append(
            f"  {outcome} {sign} {cat_tag}rate={rate:.2f} :: {q_text}"
        )
    return "\n".join(lines)


def format_history_block(history: list[dict]) -> str:
    """Render past iterations (already blinded — caller strips test_* fields)."""
    if not history:
        return "(no prior iterations — this is the first improvement attempt)"
    lines = []
    for h in history:
        desc = h.get("description", "")
        snippet = desc[:200] + ("..." if len(desc) > 200 else "")
        total = h["train_passed"] + h["train_failed"]
        lines.append(
            f"  iter {h['iter']}: train_passed={h['train_passed']}/{total}\n"
            f"    desc: {snippet}"
        )
    return "\n".join(lines)


def strip_test_fields(history: list[dict]) -> list[dict]:
    """Defense-in-depth: drop any test_* keys + raw results before prompting."""
    blinded = []
    for h in history:
        clean = {k: v for k, v in h.items() if not k.startswith("test_")}
        clean.pop("results", None)  # raw results may include test queries
        blinded.append(clean)
    return blinded


def _strip_wrapping_quotes(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        text = text[1:-1].strip()
    return text


def improve_description(
    skill_dir: Path,
    train_results: list[dict],
    history: Optional[list[dict]] = None,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    description_override: Optional[str] = None,
) -> str:
    """Generate a new candidate description using Claude.

    `description_override` lets the loop pass the *current iteration's* desc
    (which is not yet on disk) instead of always re-reading SKILL.md.
    """
    name, description, _ = parse_skill_md(skill_dir)
    if description_override is not None:
        description = description_override
    if not name:
        raise ValueError(f"SKILL.md at {skill_dir} missing name")

    blinded = strip_test_fields(history or [])
    train_block = format_results_block(train_results)
    history_block = format_history_block(blinded)
    prompt = PROMPT_TEMPLATE.format(
        skill_name=name,
        description=description,
        train_block=train_block,
        history_block=history_block,
        max_chars=MAX_DESCRIPTION_CHARS,
    )

    client = make_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )

    text_parts = [
        block.text for block in response.content if hasattr(block, "text")
    ]
    text = _strip_wrapping_quotes("".join(text_parts))

    if "<" in text or ">" in text:
        raise ValueError(
            "LLM returned a description containing angle brackets — "
            "would break YAML frontmatter. Raw output:\n" + text
        )
    if len(text) > MAX_DESCRIPTION_CHARS:
        raise ValueError(
            f"LLM returned description of {len(text)} chars "
            f"(max {MAX_DESCRIPTION_CHARS}). Raw output:\n" + text
        )

    return text


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rewrite a skill description from training failures."
    )
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("train_results", type=Path,
                        help="JSON: either run_eval output or a list of result dicts")
    parser.add_argument("--history", type=Path, default=None,
                        help="Optional history.json from prior iterations")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    args = parser.parse_args()

    raw = json.loads(args.train_results.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        train_results = raw.get("results", [])
    else:
        train_results = raw

    history: list[dict] = []
    if args.history:
        h_raw = json.loads(args.history.read_text(encoding="utf-8"))
        if isinstance(h_raw, dict):
            history = h_raw.get("iterations", [])
        else:
            history = h_raw

    new_desc = improve_description(
        args.skill_dir, train_results, history,
        model=args.model,
    )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(new_desc, encoding="utf-8")
        print(f"New description written to {args.out}", file=sys.stderr)
        print(f"Length: {len(new_desc)} chars", file=sys.stderr)
    else:
        print(new_desc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
