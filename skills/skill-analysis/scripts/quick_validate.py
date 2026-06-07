#!/usr/bin/env python3
"""Quick SKILL.md validation for skill-analysis Phase 6.

Static frontmatter compliance check (no LLM, no subprocess). Useful before
running Phase 6 to catch malformed frontmatter early.

Ported from skill-creator/scripts/quick_validate.py with identical rules:
- name: kebab-case, ≤64 chars, no leading/trailing/double hyphens
- description: ≤1024 chars, no angle brackets
- frontmatter keys: name, description, license, allowed-tools, metadata, compatibility

Usage:
    python -m scripts.quick_validate <skill_directory>
"""

import sys
import re
from pathlib import Path

import yaml


ALLOWED_PROPERTIES = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "compatibility",
    "version",  # skill-analysis convention; tolerated
}


def validate_skill(skill_path):
    """Basic validation of a skill directory.

    Returns:
        (bool, str): (is_valid, message)
    """
    skill_path = Path(skill_path)

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: "
            f"{', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    if "name" not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if "description" not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        if not re.match(r"^[a-z0-9-]+$", name):
            return False, (
                f"Name '{name}' should be kebab-case "
                f"(lowercase letters, digits, and hyphens only)"
            )
        if name.startswith("-") or name.endswith("-") or "--" in name:
            return False, (
                f"Name '{name}' cannot start/end with hyphen "
                f"or contain consecutive hyphens"
            )
        if len(name) > 64:
            return False, (
                f"Name is too long ({len(name)} characters). Maximum is 64."
            )

    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        return False, (
            f"Description must be a string, got {type(description).__name__}"
        )
    description = description.strip()
    if description:
        if "<" in description or ">" in description:
            return False, "Description cannot contain angle brackets (< or >)"
        if len(description) > 1024:
            return False, (
                f"Description is too long ({len(description)} characters). "
                f"Maximum is 1024."
            )

    compatibility = frontmatter.get("compatibility", "")
    if compatibility:
        if not isinstance(compatibility, str):
            return False, (
                f"Compatibility must be a string, got "
                f"{type(compatibility).__name__}"
            )
        if len(compatibility) > 500:
            return False, (
                f"Compatibility is too long ({len(compatibility)} characters). "
                f"Maximum is 500."
            )

    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.quick_validate <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
