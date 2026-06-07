# Trigger Pattern Catalog — Specificity, Balance, and Disambiguation

## The Core Problem: Precision vs. Recall in Triggers

Skill trigger design is fundamentally a precision/recall tradeoff:

```
High Precision + High Recall = Ideal (rare)
High Precision + Low Recall  = Too narrow (misses valid use cases)
Low Precision + High Recall = Too broad (fires on everything)
Low Precision + Low Recall = Useless
```

The goal: maximum recall without sacrificing precision.

---

## Pattern 1: The Verb-Object Trigger

**Structure:** `<action verb> <noun/entity>`

**Examples:**
- "create a hook"
- "write a test"
- "add an endpoint"
- "fix the bug"
- "build a component"

**Why it works:** Verbs are high-intent signals. "create", "write", "add" are almost never used by accident.

**Risk:** Common verbs without context → false positives.
- "create" alone → too broad
- "create a hook" → good
- "create a PreToolUse hook" → specific

**Rule:** Always pair a verb with a noun or domain-specific entity.

---

## Pattern 2: The Entity Mention Trigger

**Structure:** `<domain-specific noun or proper name>`

**Examples:**
- "Playwright"
- "Monaco Editor"
- "PreToolUse hook"
- "Zod schema"
- "Claude Code"

**Why it works:** Domain entities are self-filtering. "Playwright" in context almost always means the user wants browser automation.

**Risk:** Generic entity names → false positives.
- "test" → too generic (unit test? load test? A/B test?)
- "Playwright" → good if domain is browser automation
- "PreToolUse" → good because it's a proper noun with a specific meaning

**Rule:** Only use entity triggers when the entity name is unambiguous within the skill's domain.

---

## Pattern 3: The Scenario Trigger

**Structure:** `<user goal expressed as a scenario>`

**Examples:**
- "debug a flaky test"
- "set up CI for the first time"
- "migrate from Jest to Vitest"
- "optimize database query performance"

**Why it works:** Scenario triggers capture the *intent* behind the request, not just the surface words.

**Risk:** Scenarios must be common enough that users naturally describe them this way.
- "migrate to X" is a common pattern — good trigger
- "I have 47 failing tests after upgrading" — too specific to be a trigger

**Rule:** Scenario triggers should map to user goals, not edge-case descriptions.

---

## Pattern 4: The Negative Trigger (What NOT to Match)

Some skills should explicitly NOT fire in certain contexts. While there's no native "negative trigger" syntax, you can achieve this through specificity:

```
# Instead of (too broad):
"test"  → fires on "write me a test email"

# Do this (contextual):
"write a browser test", "run playwright tests", "add an E2E test"
→ only fires when testing context is present
```

---

## Specificity Spectrum

```
Too Narrow ←————————————————————————→ Too Broad

"add a Claude Code PreToolUse hook    "hook"
  for validating API keys on 2024-06-15"
                                      "test"
    "playwright e2e test"
           "write a browser test"
                   "add E2E tests"
```

**Finding the sweet spot:**

| Too Narrow | Good | Too Broad |
|---|---|---|
| < 3 trigger phrases | 4–10 trigger phrases | > 20 trigger phrases |
| Single phrasing variation | Action + entity + scenario | Generic single words |
| Domain-specific jargon only | Mix of jargon and natural language | Common English words |
| Misses valid use cases | Covers core use cases | Fires on unrelated requests |

---

## False Positive Mitigation

False positives = skill fires when it shouldn't. Consequences: noise, wasted context, wrong workflow loaded.

### Common FP Causes and Fixes

**Cause 1: Single common word as trigger**
```
# ❌ FP risk: HIGH
description: "fix"

# ✅ Fix: Pair with context
description: "fix a hook", "fix PreToolUse", "hook not firing"
```

**Cause 2: Ambiguous word without domain qualifier**
```
# ❌ FP risk: HIGH
description: "review"

# ✅ Fix: Add domain context
description: "code review", "PR review", "review a pull request"
```

**Cause 3: Overlapping with a more general skill**
```
# If skill A is "hook-development" and skill B is "claude-code-debugging":
# ❌ "debug" appears in both → ambiguous
# ✅ Hook skill: "debug a hook", "hook not firing"
#    Debug skill: "debug the API", "debug connection issues"
```

### FP Risk Checklist

For each trigger phrase, answer:
1. Could this phrase appear in an unrelated conversation? (Yes → FP risk)
2. Does the phrase contain a domain-specific noun or qualifier? (No → FP risk)
3. Is the phrase a single common verb without object? (Yes → FP risk)

---

## False Negative Mitigation

False negatives = skill should fire but doesn't. Consequences: lost opportunity, wrong skill or no skill loaded.

### Common FN Causes and Fixes

**Cause 1: Only one phrasing variant**
```
# ❌ FN risk: HIGH (users say the same thing many ways)
description: "create a hook"

# ✅ Fix: Cover action synonyms
description: "create a hook", "add a hook", "register a hook", "set up a hook"
```

**Cause 2: Missing debugging/maintenance triggers**
```
# ❌ FN risk: MEDIUM (skill only covers creation, not usage)
description: "create a hook"

# ✅ Fix: Add lifecycle triggers
description: "create a hook", "add a hook", "debug a hook", "test my hooks",
  "check which hooks are active", "remove a hook"
```

**Cause 3: Missing scenario-based triggers**
```
# ❌ FN risk: MEDIUM (users think in goals, not actions)
description: "rotate a PDF"

# ✅ Fix: Add goal-based triggers
description: "rotate a PDF", "fix PDF orientation", "my PDF is sideways",
  "rotate pages in a PDF document"
```

### FN Risk Checklist

For each trigger phrase, answer:
1. Would a user naturally say this phrase? (No → FN risk)
2. Are there common synonyms this phrase doesn't cover? (Yes → FN risk)
3. Does the skill cover only creation but not debugging? (Yes → FN risk)

---

## Cross-Skill Disambiguation

When multiple skills share overlapping triggers, the system may fire the wrong one.

### Detection Method

List all skills in the same plugin. For each, extract trigger phrases. Flag overlaps.

```
Skill A: "create a hook", "add a hook", "debug a hook"
Skill B: "hook review", "check hooks", "debug hooks"

Overlap detected: "hook" (entity) + "debug" (verb)
```

### Resolution Strategies

| Strategy | When to Use | Example |
|----------|-------------|---------|
| **Narrow the entity** | Skills share verb but differ in entity | "create a hook" vs "create a PR" |
| **Narrow the verb** | Skills share entity but differ in action | "create a hook" vs "review hooks" |
| **Move one trigger** | One phrase belongs in a different skill | Move "debug hooks" to hook-debugging skill |
| **Merge skills** | Two skills always fire together | Merge into one skill with two workflow sections |
| **Keep separate** | Overlap is minor, both are valid | Different contexts make disambiguation work |

---

## Trigger Evolution Over Time

Triggers should evolve as usage patterns emerge.

### Signal Sources for Trigger Updates

1. **User feedback:** "I asked X but the skill didn't fire"
2. **System logs:** Skill X fires but user immediately switches context
3. **Similar skill overlap:** New skill shares too many triggers with existing one
4. **Domain changes:** New terminology enters the domain

### Versioning Triggers

When changing trigger phrases in a released skill:
- Document old → new phrase mapping
- Consider deprecation period (keep old phrase for 1–2 versions)
- Update `version` field (patch for minor additions, minor for phrase changes)
- Note breaking changes in a `CHANGELOG.md` or changelog section

```
# Example: Evolving trigger phrases

v0.1.0 (initial):
  - "create a hook"
  - "add a hook"

v0.2.0 (add debugging):
  - "create a hook"
  - "add a hook"
  - "debug a hook"        ← NEW
  - "hook not working"    ← NEW

v1.0.0 (breaking — remove ambiguity):
  - "create a Claude Code hook"   ← CHANGED: added "Claude Code"
  - "add a Claude Code hook"      ← CHANGED: added "Claude Code"
  - "debug a hook"
  (Note: removed "hook" alone — too ambiguous with webhook tools)
```

---

## Quick Reference: Trigger Quality Rubric

| Dimension | Poor (0) | Fair (1) | Good (2) |
|-----------|----------|----------|----------|
| **Specificity** | Single common word, no context | Some context, 1-2 phrases | 4+ phrases with context |
| **Coverage** | Misses common variants | Covers most variants | All common variants + scenarios |
| **Disambiguation** | Overlaps with 3+ skills | Overlaps with 1-2 skills | No overlap or intentionally resolved |
| **Natural language** | Technical jargon only | Mix of jargon and natural | User's natural phrasing |
| **Completeness** | Creation only | Creation + one lifecycle stage | Full lifecycle + debugging |
