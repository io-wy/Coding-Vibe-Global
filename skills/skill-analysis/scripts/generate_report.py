"""Phase 6 sub-phase 6e: render an HTML report from run_loop history.

Reads a `history.json` produced by `run_loop.py` and emits a single self-contained
HTML page: rows are iterations, columns are queries (train then test, with a
visual split). Best iteration is highlighted. Auto-refresh optional so io-wy can
watch the loop progress live.

Schema differences from skill-creator's report:
- iterations live under `iterations` not `history`
- per-iteration `results` is the full list (train+test combined); we split by
  `train_set` / `test_set` query lists
- iteration counter is `iter` not `iteration`

Usage:
    python -m scripts.generate_report <history.json> --out report.html [--auto-refresh]
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
{refresh_tag}<title>{title_prefix}Skill Description Optimization</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600&family=Lora:wght@400;500&display=swap" rel="stylesheet">
<style>
body {{ font-family: 'Lora', Georgia, serif; max-width: 100%; margin: 0 auto; padding: 20px; background: #faf9f5; color: #141413; }}
h1 {{ font-family: 'Poppins', sans-serif; }}
.explainer, .summary {{ background: white; padding: 15px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #e8e6dc; }}
.explainer {{ color: #5a5851; font-size: 0.875rem; line-height: 1.6; }}
.summary p {{ margin: 5px 0; }}
.best {{ color: #788c5d; font-weight: bold; }}
.table-container {{ overflow-x: auto; width: 100%; }}
table {{ border-collapse: collapse; background: white; border: 1px solid #e8e6dc; border-radius: 6px; font-size: 12px; min-width: 100%; }}
th, td {{ padding: 8px; text-align: left; border: 1px solid #e8e6dc; word-wrap: break-word; }}
th {{ font-family: 'Poppins', sans-serif; background: #141413; color: #faf9f5; font-weight: 500; }}
th.test-col {{ background: #6a9bcc; }}
th.query-col {{ min-width: 200px; }}
td.description {{ font-family: monospace; font-size: 11px; max-width: 400px; }}
td.result {{ text-align: center; font-size: 16px; min-width: 40px; }}
td.test-result {{ background: #f0f6fc; }}
.pass {{ color: #788c5d; }}
.fail {{ color: #c44; }}
.rate {{ font-size: 9px; color: #b0aea5; display: block; }}
tr:hover {{ background: #faf9f5; }}
.score {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
.score-good {{ background: #eef2e8; color: #788c5d; }}
.score-ok {{ background: #fef3c7; color: #d97706; }}
.score-bad {{ background: #fceaea; color: #c44; }}
.best-row {{ background: #f5f8f2; }}
th.positive-col {{ border-bottom: 3px solid #788c5d; }}
th.negative-col {{ border-bottom: 3px solid #c44; }}
.legend {{ font-family: 'Poppins', sans-serif; display: flex; gap: 20px; margin: 10px 0; font-size: 13px; align-items: center; }}
.legend-item {{ display: flex; align-items: center; gap: 6px; }}
.legend-swatch {{ width: 16px; height: 16px; border-radius: 3px; display: inline-block; }}
.swatch-positive {{ background: #141413; border-bottom: 3px solid #788c5d; }}
.swatch-negative {{ background: #141413; border-bottom: 3px solid #c44; }}
.swatch-test {{ background: #6a9bcc; }}
.swatch-train {{ background: #141413; }}
</style>
</head>
<body>
<h1>{title_prefix}Skill Description Optimization</h1>
<div class="explainer">
<strong>Phase 6 empirical loop.</strong> Each row is one iteration. Columns are
eval queries: green checkmarks mean the runtime model triggered correctly (or
correctly didn't trigger), red crosses mean it got it wrong. Train columns are
visible to the description-rewriter; test columns are held out (best iteration
is selected by test score to prevent overfitting).
</div>
"""


def _score_class(correct: int, total: int) -> str:
    if total <= 0:
        return "score-bad"
    ratio = correct / total
    if ratio >= 0.8:
        return "score-good"
    if ratio >= 0.5:
        return "score-ok"
    return "score-bad"


def _aggregate_runs(results: list[dict]) -> tuple[int, int]:
    correct = 0
    total = 0
    for r in results:
        runs = int(r.get("runs", 0))
        triggers = int(r.get("triggers", 0))
        total += runs
        if r.get("should_trigger", True):
            correct += triggers
        else:
            correct += runs - triggers
    return correct, total


def _split_results(
    results: list[dict],
    train_queries: set[str],
    test_queries: set[str],
) -> tuple[list[dict], list[dict]]:
    train_r = [r for r in results if r["query"] in train_queries]
    test_r = [r for r in results if r["query"] in test_queries]
    return train_r, test_r


def _render_query_header(qinfo: dict, *, is_test: bool) -> str:
    polarity = "positive-col" if qinfo["should_trigger"] else "negative-col"
    extra = "test-col " if is_test else ""
    return (
        f'<th class="{extra}{polarity}">'
        f'{html.escape(qinfo["query"])}</th>\n'
    )


def _render_result_cell(r: dict, *, is_test: bool) -> str:
    did_pass = bool(r.get("pass", False))
    triggers = int(r.get("triggers", 0))
    runs = int(r.get("runs", 0))
    icon = "✓" if did_pass else "✗"
    css = "pass" if did_pass else "fail"
    extra = " test-result" if is_test else ""
    return (
        f'<td class="result{extra} {css}">{icon}'
        f'<span class="rate">{triggers}/{runs}</span></td>\n'
    )


def generate_html(
    data: dict,
    *,
    auto_refresh: bool = False,
    skill_name: str = "",
) -> str:
    iterations: list[dict] = data.get("iterations", [])
    train_set: list[dict] = data.get("train_set", [])
    test_set: list[dict] = data.get("test_set", [])
    train_queries = {e["query"] for e in train_set}
    test_queries = {e["query"] for e in test_set}

    title_prefix = (
        html.escape(skill_name + " — ")
        if skill_name else
        html.escape(data.get("skill_name", "") + " — ") if data.get("skill_name") else ""
    )
    refresh_tag = '<meta http-equiv="refresh" content="5">\n' if auto_refresh else ""

    parts: list[str] = [HEAD.format(refresh_tag=refresh_tag, title_prefix=title_prefix)]

    # Summary
    original_desc = iterations[0]["description"] if iterations else "(no iterations)"
    best_desc = data.get("best_description", "(no best yet)")
    best_iter = data.get("best_iteration", "?")
    best_train = data.get("best_train_passed", "?")
    best_train_fail = data.get("best_train_failed", "?")
    best_test = data.get("best_test_passed", "?")
    best_test_fail = data.get("best_test_failed", "?")
    parts.append(f"""
<div class="summary">
<p><strong>Original:</strong> <code>{html.escape(str(original_desc))}</code></p>
<p class="best"><strong>Best (iter #{best_iter}):</strong> <code>{html.escape(str(best_desc))}</code></p>
<p><strong>Best score:</strong> train {best_train}/{(best_train or 0)+(best_train_fail or 0)} · test {best_test}/{(best_test or 0)+(best_test_fail or 0)}</p>
<p><strong>Iterations run:</strong> {len(iterations)} | <strong>Train size:</strong> {len(train_set)} | <strong>Test size:</strong> {len(test_set)} | <strong>Holdout:</strong> {data.get('holdout', '?')} | <strong>Seed:</strong> {data.get('seed', '?')}</p>
</div>
<div class="legend">
<span style="font-weight:600">Legend:</span>
<span class="legend-item"><span class="legend-swatch swatch-positive"></span>Should trigger</span>
<span class="legend-item"><span class="legend-swatch swatch-negative"></span>Should NOT trigger</span>
<span class="legend-item"><span class="legend-swatch swatch-train"></span>Train</span>
<span class="legend-item"><span class="legend-swatch swatch-test"></span>Test (held out)</span>
</div>
<div class="table-container">
<table>
<thead>
<tr>
<th>Iter</th>
<th>Train</th>
<th>Test</th>
<th class="query-col">Description</th>
""")

    for q in train_set:
        parts.append(_render_query_header(q, is_test=False))
    for q in test_set:
        parts.append(_render_query_header(q, is_test=True))

    parts.append("</tr>\n</thead>\n<tbody>\n")

    for h in iterations:
        results = h.get("results", [])
        train_r, test_r = _split_results(results, train_queries, test_queries)
        train_correct, train_total = _aggregate_runs(train_r)
        test_correct, test_total = _aggregate_runs(test_r)
        train_class = _score_class(train_correct, train_total)
        test_class = _score_class(test_correct, test_total)
        row_class = "best-row" if h.get("iter") == best_iter else ""
        desc = h.get("description", "")

        parts.append(
            f'<tr class="{row_class}">'
            f'<td>{h.get("iter", "?")}</td>'
            f'<td><span class="score {train_class}">{train_correct}/{train_total}</span></td>'
            f'<td><span class="score {test_class}">{test_correct}/{test_total}</span></td>'
            f'<td class="description">{html.escape(desc)}</td>\n'
        )

        train_by_q = {r["query"]: r for r in train_r}
        test_by_q = {r["query"]: r for r in test_r}
        for q in train_set:
            r = train_by_q.get(q["query"], {"pass": False, "triggers": 0, "runs": 0})
            parts.append(_render_result_cell(r, is_test=False))
        for q in test_set:
            r = test_by_q.get(q["query"], {"pass": False, "triggers": 0, "runs": 0})
            parts.append(_render_result_cell(r, is_test=True))

        parts.append("</tr>\n")

    parts.append("</tbody>\n</table>\n</div>\n</body>\n</html>\n")
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a Phase 6 history.json as HTML report."
    )
    parser.add_argument("input", type=str,
                        help="Path to history.json (or '-' for stdin)")
    parser.add_argument("--out", type=Path, default=None,
                        help="Output HTML file (default: stdout)")
    parser.add_argument("--auto-refresh", action="store_true",
                        help="Add 5s meta-refresh so live runs visibly update")
    parser.add_argument("--skill-name", type=str, default="",
                        help="Override skill name in title (defaults to data.skill_name)")
    args = parser.parse_args()

    if args.input == "-":
        data = json.load(sys.stdin)
    else:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))

    output = generate_html(data, auto_refresh=args.auto_refresh, skill_name=args.skill_name)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"Report written to {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
