# Skill Evolution Guide — Lifecycle, Versioning, and Iteration

## Skill Lifecycle Model

Every skill moves through four phases:

```
Draft → Alpha → Stable → Deprecated
  ↑                            ↓
  ←——————— Revised ←———————————
```

| Phase | Criteria | Version Prefix |
|-------|----------|----------------|
| **Draft** | Initial implementation, not tested in production | 0.0.x |
| **Alpha** | Tested internally, known limitations documented | 0.x.x |
| **Stable** | Production-ready, backward-compatible changes only | 1.x.x+ |
| **Deprecated** | Superseded by another skill or no longer maintained | — |

---

## When and How to Version

### Semantic Versioning for Skills

```
version: MAJOR.MINOR.PATCH

MAJOR — Breaking changes to triggers, workflow, or structure
MINOR — Additive changes (new triggers, new references, new examples)
PATCH — Corrections (fix typos, fix broken links, clarify instructions)
```

### What Constitutes Each Change Type

| Change | Type | Example |
|--------|------|---------|
| Add trigger phrase | MINOR | +"debug a hook" to hook-development |
| Remove trigger phrase | MAJOR | -"hook" alone (too ambiguous) |
| Rename skill | MAJOR | skill-hooks → hook-manager |
| Restructure directories | MAJOR | Move content from SKILL.md to references/ |
| Add reference file | MINOR | New references/troubleshooting.md |
| Fix typo in description | PATCH | "debugg" → "debug" |
| Fix broken script | PATCH | Fix import error in scripts/validate.sh |
| Expand core workflow | MINOR | Add step 5 to 3-step workflow |
| Add examples/ directory | MINOR | First example added |

---

## The Iteration Loop

Skill improvement follows a observe → diagnose → act → validate cycle.

### Step 1: Observe — Gather Signals

Collect signals from two sources:

**Direct feedback:**
- User says "the skill didn't fire when I expected it to"
- User says "the skill fired but gave wrong guidance"
- User ignores skill output and does task manually

**Indirect signals:**
- Skill fires but user context-switches immediately after
- Skill output is accepted without modification (good signal)
- Skill output needs heavy editing before use

### Step 2: Diagnose — Run the Analysis Skill

Use the skill-analysis framework to systematically evaluate:

1. Trigger & description analysis (Phase 1)
2. Structural quality analysis (Phase 2)
3. Recall rate estimation (Phase 3)

### Step 3: Act — Prioritize and Fix

Execute the evolution plan from Phase 4 of the analysis framework. Fix in priority order:
1. Blockers first (description format, missing fields)
2. High-severity issues next (recall score <70, conflicts)
3. Medium-severity issues (structural improvements)
4. Low-severity issues (style polish, orphan files)

### Step 4: Validate — Test Before Shipping

**Test trigger changes:**
```
Before shipping a trigger update, test:
1. Does the new phrase fire correctly on intended requests?
2. Does it fire on any unintended requests?
3. Do existing phrases still fire correctly?
4. Does the change create conflict with sibling skills?
```

**Test structural changes:**
```
Before shipping a content reorganization:
1. Read SKILL.md end-to-end — does it still flow logically?
2. Do all references/ pointers still point to existing files?
3. Is SKILL.md still within 1,500-2,000 words?
4. Do examples still run without modification?
```

---

## Trigger Evolution Strategies

### Strategy 1: Expand Coverage (False Negative Fix)

When users say the skill didn't fire, add their phrasing as a trigger:

```
# Current:
"create a hook", "add a hook"

# After user feedback "I said 'register a hook' and nothing happened":
"create a hook", "add a hook", "register a hook"
```

### Strategy 2: Narrow Context (False Positive Fix)

When the skill fires on unrelated requests, add context qualifiers:

```
# Current:
"build a component"

# After false positive "I said 'build a house' and component skill fired":
"build a React component", "build a UI component", "create a component"
```

### Strategy 3: Deprecate and Replace

When a trigger phrase becomes outdated or ambiguous:

```
# Version 0.x — original
"hook"

# Version 1.0 — deprecated "hook" in favor of "Claude Code hook"
# Keep old phrase for one minor version as fallback
"Claude Code hook", "claude hook"
# Note in evolution plan: remove "hook" alone in v2.0
```

### Strategy 4: Merge Overlapping Skills

When two skills are always used together:

```
# Before:
skill-a/  — "create a thing", "add a thing"
skill-b/  — "configure a thing", "set up a thing"

# After: Merge into one skill
thing-manager/
  — "create a thing", "add a thing"
  — "configure a thing", "set up a thing"
  — "manage a thing"
```

---

## Content Evolution Strategies

### Strategy 1: Progressive Disclosure Refinement

If SKILL.md is >3,000 words, move content to references/:

```
# Before: SKILL.md = 4,200 words (bloated)

# After:
SKILL.md = 1,800 words
  + references/
      advanced-patterns.md  (1,400 words — extracted from SKILL.md)
      troubleshooting.md    (800 words — extracted from SKILL.md)
```

### Strategy 2: Example-Driven Learning

If a reference is theoretical and hard to follow, add examples:

```
# Before:
references/api.md — 800 words of API description

# After:
references/api.md — 500 words of API description
examples/api-usage.sh — 60 lines of working example
```

### Strategy 3: Orphan File Recovery

If a references/ file exists but is never referenced, either:
- Add a reference to it in SKILL.md (if useful)
- Move its content into SKILL.md or another file (if small)
- Delete it (if truly unnecessary)

---

## Testing Triggers Without Production

Since there's no native A/B testing framework for skills, simulate trigger evaluation:

### Manual Trigger Test Matrix

For each trigger phrase, test against:

| Test Input | Expected Action |
|------------|-----------------|
| Exact phrase in quotes | Should trigger |
| Phrase with surrounding context | Should trigger |
| Phrase spoken naturally ("I want to create a hook") | Should trigger |
| Unrelated request containing the phrase | Should NOT trigger |
| Similar but different phrase | Should NOT trigger |

```
Example test matrix for "create a hook":

✓ "create a hook"                          → TRIGGER
✓ "I want to create a hook for my project" → TRIGGER
✓ "how do I create a hook in Claude Code"  → TRIGGER
✗ "create a webhook instead"                → NO TRIGGER (different entity)
✗ "create a GitHub hook"                    → TRIGGER? (depends on domain —
                                              if hook skill is Claude Code specific,
                                              this is a FN, not a FP)
```

### Cross-Skill Trigger Collision Test

Test all skills in the same plugin against the same input:

```
Test input: "debug my hooks"

Expected: skill-hook-debugging fires
Acceptable: skill-hook-development also fires (has "debug a hook")
Not acceptable: skill-debugging (generic) fires instead of skill-hook-*
```

---

## Breaking Changes Policy

Breaking changes to triggers should be rare and well-communicated.

### What Counts as Breaking

- Removing a trigger phrase (users who relied on it get no match)
- Changing a trigger phrase significantly (same as remove + add)
- Renaming the skill (breaks all external references)
- Removing a reference file that users depend on
- Changing the core workflow fundamentally

### How to Handle Breaking Changes

1. Announce in the skill's changelog (even if informal)
2. Keep old trigger for 1–2 versions before removal
3. Update `version` to next MAJOR
4. Document migration path in `references/migration.md`

---

## Skill Health Metrics

Without production telemetry, estimate health from static analysis:

| Metric | Good | Warning | Critical |
|--------|------|---------|---------|
| Description word count | 30–150 words | 150–300 words | <20 or >300 |
| SKILL.md word count | 1,500–2,000 | 2,000–3,000 | >3,000 or <500 |
| Trigger phrase count | 4–15 | 2–3 or 15–30 | 1 or >30 |
| Recall score (heuristic) | 85–100 | 70–84 | <70 |
| Progressive disclosure | All refs referenced | Some orphan files | SKILL.md monolithic |
| Version field | Present | — | Missing |

---

## Quick Reference: Evolution Action Types

| Action | Frequency | Version Bump | Risk |
|--------|-----------|-------------|------|
| Add trigger phrase | Common | MINOR | Low |
| Remove ambiguous trigger | Occasional | MAJOR | Medium |
| Move content to references/ | Common | MINOR | Low |
| Rename skill | Rare | MAJOR | High |
| Add example file | Common | MINOR | Low |
| Add reference file | Common | MINOR | Low |
| Delete orphan file | Occasional | PATCH | Low |
| Fix typo | Common | PATCH | None |
| Expand core workflow | Occasional | MINOR | Low |
| Rewrite entire skill | Rare | MAJOR | High |
