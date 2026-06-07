"""Shared utilities for skill-analysis Phase 6 scripts.

Ported from skill-creator/scripts/utils.py — same parsing logic since SKILL.md
frontmatter format is identical across the Anthropic skill ecosystem.
"""

import os
from pathlib import Path
from typing import Any


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content).

    Handles YAML multiline indicators (>, |, >-, |-) by joining indented
    continuation lines into a single description string.

    Raises:
        ValueError: if frontmatter is missing or malformed.
    """
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (
                    frontmatter_lines[i].startswith("  ")
                    or frontmatter_lines[i].startswith("\t")
                ):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content


def make_client() -> Any:
    """Build an Anthropic SDK client honoring Claude Code's native auth vars.

    Resolution order for credentials:
      1. ANTHROPIC_API_KEY (SDK default)
      2. ANTHROPIC_AUTH_TOKEN (Claude Code's CLI-side var)

    If ANTHROPIC_BASE_URL is set, the client routes there — useful when Claude
    Code is configured against a compatible proxy (e.g. Kimi). Phase 6 then
    measures the proxy endpoint's behavior, not necessarily real Anthropic
    Claude — re-run Phase 6 against the deployment endpoint of interest to
    confirm a description still triggers correctly there.

    anthropic SDK is imported lazily so quick_validate.py (no LLM) stays free
    of the dependency.
    """
    import anthropic  # local import: avoid forcing dep on quick_validate

    api_key = os.environ.get("ANTHROPIC_API_KEY") \
        or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    kwargs: dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    return anthropic.Anthropic(**kwargs)
