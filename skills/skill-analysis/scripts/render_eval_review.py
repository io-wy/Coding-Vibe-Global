"""Phase 6 sub-phase 6a helper: render assets/eval_review.html with placeholders filled.

Reads:
  - target SKILL.md (for skill name + current description)
  - eval_set.json drafted by 6a

Writes a populated HTML file io-wy can open in a browser to edit the eval set
before launching run_loop. The browser exports back to a JSON file (no server
required — pure client-side download).

Usage:
    python -m scripts.render_eval_review <skill_dir> <eval_set.json> --out review.html
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .utils import parse_skill_md


def render(template_path: Path, skill_name: str, description: str, eval_data: list[dict]) -> str:
    template = template_path.read_text(encoding="utf-8")
    eval_json = json.dumps(eval_data, ensure_ascii=False, indent=2)
    return (
        template
        .replace("__SKILL_NAME_PLACEHOLDER__", skill_name)
        .replace("__SKILL_DESCRIPTION_PLACEHOLDER__", description)
        .replace("__EVAL_DATA_PLACEHOLDER__", eval_json)
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Populate eval_review.html with skill metadata + eval set."
    )
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("eval_set", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=None,
                        help="Override template path (defaults to ../assets/eval_review.html)")
    args = parser.parse_args()

    name, description, _ = parse_skill_md(args.skill_dir)
    if not name:
        print(f"SKILL.md at {args.skill_dir} has no name", file=sys.stderr)
        return 1

    eval_data = json.loads(args.eval_set.read_text(encoding="utf-8"))
    if not isinstance(eval_data, list):
        print("eval_set must be a JSON array", file=sys.stderr)
        return 1

    template_path = args.template or (
        Path(__file__).resolve().parent.parent / "assets" / "eval_review.html"
    )
    if not template_path.exists():
        print(f"Template not found: {template_path}", file=sys.stderr)
        return 1

    html = render(template_path, name, description, eval_data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out} ({len(html)} bytes)", file=sys.stderr)
    print(
        f"Open in browser:  start \"\" \"{args.out}\"  (Windows) "
        f"or  open {args.out}  (macOS)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
