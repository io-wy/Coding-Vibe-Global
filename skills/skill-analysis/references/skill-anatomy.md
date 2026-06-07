# Skill Anatomy — What Makes a Well-Formed Skill

## The Four Components of a Skill

Every skill has exactly four components, each serving a distinct purpose:

```
skill-name/
├── SKILL.md (required)          — Trigger metadata + core procedural knowledge
├── references/ (optional)       — Detailed reference material, loaded as needed
├── examples/ (optional)         — Working code/config snippets, copy-paste ready
└── scripts/ (optional)          — Executable utilities, run without loading into context
```

Understanding where content belongs is the core of skill design.

---

## SKILL.md Anatomy

### Required: YAML Frontmatter

```yaml
---
name: hook-development
description: This skill should be used when the user asks to "create a hook",
  "add a PreToolUse hook", "validate tool use", "implement prompt-based hooks",
  or mentions hook events (PreToolUse, PostToolUse, Stop).
version: 0.1.0
---
```

**Every field explained:**

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Skill identifier, used in logs and debugging |
| `description` | Yes | Trigger decision engine input — the ONLY thing always in context |
| `version` | Recommended | Tracks evolution; follow semver |

**The description is not a summary. It is the trigger signal.**

### SKILL.md Body: Core Anatomy

A well-structured SKILL.md body follows this section order:

```
# <Skill Name>

<purpose paragraph — 2-3 sentences max>

## When to Activate
<explicit list of trigger scenarios>

## Core Workflow
<numbered steps for the main use case>

## Best Practices
<3-5 specific do's and don'ts>

## Common Mistakes
<mistakes with corrections>

## Quick Reference
<one-liners, tables, checklists for frequent operations>

## Additional Resources
### References
- **references/<file>.md** — <one-line description>
### Examples
- **examples/<file>.sh** — <one-line description>
```

### Length Guidelines

| Content Type | Target | Maximum |
|---|---|---|
| SKILL.md body | 1,500–2,000 words | 3,000 words |
| references/*.md | 2,000–5,000 words each | No hard limit |
| examples/* | As needed | — |
| scripts/* | As needed | — |

If SKILL.md exceeds 3,000 words without references/ backing it up → **structural failure**.

---

## Description Quality: Annotated Examples

### Example 1 — Good: Specific, Third-Person, Diverse Triggers

```yaml
description: >
  This skill should be used when the user asks to "create a hook",
  "add a PreToolUse hook", "validate hook scripts", "implement a PostToolUse hook",
  "check which hooks are firing", "debug a hook", or mentions hook events
  like PreToolUse, PostToolUse, or Stop.
```

**Why good:**
- ✅ Third-person ("This skill should be used when...")
- ✅ 7 specific trigger phrases covering synonyms and variations
- ✅ Includes both action phrases ("create", "add") and entity mentions ("hook events")
- ✅ No overlap with overly generic words without context
- ✅ Covers the range from creation to debugging

### Example 2 — Bad: Second-Person, Vague, No Triggers

```yaml
description: Use this skill when you need help with hooks. Provides guidance
  for creating and managing hooks in Claude Code.
```

**Why bad:**
- ❌ Second-person ("Use this skill when you...")
- ❌ No specific trigger phrases — what would a user actually say?
- ❌ "Provides guidance" is vague, tells nothing
- ❌ "help with hooks" is too broad, no specificity

### Example 3 — Bad: Too Narrow (False Negative Risk)

```yaml
description: This skill should be used when the user says exactly "create a mycompany-specific webhook integration hook".
```

**Why bad:**
- ✅ Third-person ✅ Specific phrases ✅ No second-person
- ❌ Absurdly narrow — users will never say this verbatim
- ❌ No synonym coverage — misses "add hook", "set up webhook", "register hook"

### Example 4 — Bad: Too Broad (False Positive Risk)

```yaml
description: This skill should be used when the user mentions "code", "development",
  "programming", "writing code", "developer", "software".
```

**Why bad:**
- ❌ Every code-related request fires this skill
- ❌ No domain specificity
- ❌ Competes with every other coding-related skill
- ❌ High false positive rate — fires on "write me an email" if "code" appears

### Example 5 — Good: Balanced with Domain Context

```yaml
description: >
  This skill should be used when the user asks to "run playwright tests",
  "write a browser test", "add an E2E test", "debug a flaky test", "set up Playwright",
  "create a page object", "run tests in CI", or mentions Playwright, browser automation,
  or end-to-end testing.
```

**Why good:**
- ✅ Covers action variants: "run", "write", "add", "create", "set up"
- ✅ Includes debugging triggers: "debug", "fix flaky"
- ✅ Includes infra triggers: "CI", "run in pipeline"
- ✅ Entity mentions: "Playwright", "page object", "browser automation"
- ✅ Domain context prevents false positives from unrelated "test" mentions

---

## Progressive Disclosure Patterns

### Pattern 1 — Minimal Skill (No Bundled Resources)

```
simple-skill/
└── SKILL.md  (1,500 words — everything is core)
```

Use for: Skills that provide primarily procedural knowledge with no detailed reference material needed.

### Pattern 2 — Standard Skill (References + Examples)

```
standard-skill/
├── SKILL.md          (1,800 words — core workflow + pointers)
├── references/
│   ├── patterns.md   (2,500 words — detailed patterns)
│   └── api.md        (1,200 words — API reference)
└── examples/
    └── basic-usage.sh (50 lines — working example)
```

Use for: Most skills. The sweet spot between context efficiency and comprehensive coverage.

### Pattern 3 — Complex Skill (References + Examples + Scripts)

```
complex-skill/
├── SKILL.md
├── references/
│   ├── patterns.md
│   ├── migration.md
│   └── troubleshooting.md
├── examples/
│   ├── simple.ts
│   └── advanced.ts
└── scripts/
    ├── validate.sh       (lint/validate skill content)
    └── generate.ts       (code generation utility)
```

Use for: Skills with validation requirements, deterministic utilities, or complex domain knowledge.

---

## Structural Anti-Patterns

### Anti-Pattern 1: SKILL.md as a Monolith

```
# ❌ Wrong
skill/
└── SKILL.md  (8,000 words — everything crammed in)
```

**Problem:** Every time the skill triggers, all 8,000 words load into context, even when only a small section is relevant.

**Fix:**
```
# ✅ Correct
skill/
├── SKILL.md          (1,800 words — core + pointers)
└── references/
    ├── patterns.md   (3,000 words)
    ├── api.md         (1,500 words)
    └── edge-cases.md  (2,000 words)
```

### Anti-Pattern 2: Orphan Reference Files

```
# ❌ Wrong
skill/
├── SKILL.md          ("See references/advanced.md for details")
└── references/
    └── advanced.md   (exists but SKILL.md never actually mentions it)
```

**Problem:** Content exists but Claude doesn't know to load it.

**Fix:** Always reference every file in SKILL.md under "Additional Resources".

### Anti-Pattern 3: Empty Directories

```
# ❌ Wrong
skill/
├── SKILL.md
├── references/       (empty — why does this exist?)
└── examples/         (empty — remove if not needed)
```

**Fix:** Remove empty directories. Only create directories you use.

### Anti-Pattern 4: SKILL.md That Ignores Its Own Resources

Even if files exist, if SKILL.md doesn't mention them, Claude won't load them:

```
# ❌ Wrong — SKILL.md body has no references section
# SKILL.md creates a complex workflow but never says
# "For detailed patterns, see references/patterns.md"
```

**Fix:** Always include an "Additional Resources" section pointing to every file.

---

## Checklist: Is My Skill Well-Formed?

Run through this before considering a skill complete:

**Frontmatter:**
- [ ] `name` field present and descriptive
- [ ] `description` uses third-person, specific trigger phrases
- [ ] `description` has no second-person errors
- [ ] `version` field present

**SKILL.md Body:**
- [ ] Purpose stated in 2–3 sentences
- [ ] "When to Activate" section exists
- [ ] Core workflow is clear and numbered
- [ ] Written in imperative form (verb-first)
- [ ] Word count: 1,500–2,000 ideal, <3,000 max
- [ ] "Additional Resources" section lists all bundled files
- [ ] All mentioned files actually exist

**Bundled Resources:**
- [ ] No orphan files (every file is referenced)
- [ ] No empty directories
- [ ] References are detailed (2,000+ words if applicable)
- [ ] Examples are complete and runnable
- [ ] Scripts are executable and documented
