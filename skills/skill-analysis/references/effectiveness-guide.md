# Effectiveness Guide — Scoring Content Quality When a Skill Fires

This guide provides detailed rubrics for Phase 2 (Effectiveness Analysis) of the skill-analysis framework. Use it when scoring workflow actionability, progressive disclosure quality, content-trigger alignment, or evaluating Enforcement/Proactive mode skills.

---

## Workflow Actionability Scoring — Annotated Examples

Each core workflow step receives a score of 0, 1, or 2.

### Score 0 — Vague

The step describes an outcome or goal without specifying *how* to achieve it. No named tool, no command, no verification signal.

**Examples:**
- *"Understand the repository structure."*
- *"Analyze the requirements."*
- *"Implement the feature."*
- *"Review the code for issues."*
- *"Set up the testing framework."*

**Why it's score 0:** Claude would read this and have no concrete action to take. It knows the destination but not the path.

### Score 1 — Specific but Incomplete

The step names an action and optionally a tool, but omits one of: the specific command/approach, or how to verify success.

**Examples:**
- *"Run `pytest` to check test results."* (no file/path scope — runs all tests?)
- *"Check the CI pipeline status."* (no command to check it)
- *"Read the configuration file."* (which file? where?)
- *"Use Playwright to run the tests."* (no command syntax)

**Why it's score 1:** These give Claude a direction but leave gaps that require inference or further investigation.

### Score 2 — Fully Actionable

The step specifies: (1) imperative verb + (2) named tool or command + (3) how to verify completion.

**Examples:**
- *"Run `python scripts/discover.py --json`. Read the `runner.framework` field. If it is missing, stop and report blocked."*
- *"Run `npx playwright test --reporter=list`. If any test in `e2e/` fails, capture the output and halt."*
- *"List all files in `references/` with `ls references/`. If the directory is empty, create a `references/` directory first."*
- *"Invoke `TaskCreate` to create a sub-task. Pass the task name, description, and output file path."*

**Why it's score 2:** Claude can execute this step without further clarification. The verification signal tells it when the step is done.

---

## Progressive Disclosure Quality — "Load When" Patterns

Progressive disclosure only works if Claude knows *when* to load a reference file. A bare file name in SKILL.md ("See references/patterns.md") is insufficient — Claude won't know if it should load it immediately or wait for a specific situation.

### The "Load When" Pattern

Each reference entry in SKILL.md should follow this format:

```
### `references/<file>.md`
Load when <condition>. Contains <what's inside>.
```

**Good examples:**
- *"Load when the skill fires and the user mentions a specific API — contains full API reference with request/response shapes."*
- *"Load when the user says 'debug' or 'fix' — contains a diagnostic decision tree for common failure modes."*
- *"Load when scoring workflow actionability — contains annotated examples of score 0/1/2 steps."*
- *"Load when the skill is being created for the first time — contains SKILL.md template with all required sections."*

**Bare reference (flag as Low severity):**
```
### References
- references/patterns.md
- references/api.md
```

**Good reference:**
```
### References
- **references/patterns.md** — Load when the user asks about implementation patterns. Contains annotated examples of anti-patterns vs. recommended patterns.
- **references/api.md** — Load when the user references a specific API name. Contains full request/response schemas.
```

### Scoring Progressive Disclosure

| Condition | Points | Notes |
|-----------|--------|-------|
| File exists AND is referenced in SKILL.md | +3 | Must appear in "References" or body text |
| Reference includes explicit "load when" / "use for" condition | +4 | Condition must be observable (e.g., user said X, skill fired) |
| File has sufficient depth (references/ ≥ 500 words) | +3 | Thin files (<200 words) contribute little |
| Cap at 25 total | — | — |

### Flagging Orphan Files

An orphan file is one that exists in `references/`, `examples/`, or `scripts/` but is never mentioned in SKILL.md.

**What to do with orphans:**
1. If the file is genuinely useful → add it to SKILL.md with a "load when" condition
2. If the file is outdated → update or delete it
3. If the file is a draft that was never completed → delete it

Never leave orphan files in a skill. They are dead weight that Claude cannot discover.

---

## Content–Trigger Alignment Checklist

For each trigger phrase in the description, verify the SKILL.md body covers it.

### Step-by-step checklist:

1. Extract all quoted trigger phrases from the description
2. For each phrase, scan the SKILL.md body
3. Classify the coverage:
   - **Full coverage** — body has a dedicated section or step for this trigger
   - **Partial coverage** — trigger is mentioned but the guidance is too brief to be actionable
   - **No coverage** — trigger is completely absent from the body

### Major Gaps (−15 each)

A major gap means the description promises a capability that the body completely ignores. This is a **High severity** issue.

**Examples:**
- Description says `"debug a flaky test"` but the body has no debugging section
- Description says `"create a hook"` but the body only explains how to review existing hooks
- Description says `"set up CI"` but the body has no CI-related content at all

**Action:** Add a section covering the missing trigger, or remove the trigger from the description if it's not a real capability.

### Partial Gaps (−7 each)

A partial gap means coverage exists but is too thin — a single sentence or vague paragraph that doesn't actually guide Claude.

**Examples:**
- `"Debugging is covered in the troubleshooting section."` → but the troubleshooting section is 3 sentences with no specific steps
- `"Check the documentation for more details."` → but no link or reference to specific documentation

**Action:** Expand the thin coverage into a full sub-section with actionable steps.

---

## Enforcement Skill Evaluation Path

Enforcement skills (trigger mode = Enforcement) use a different evaluation path that replaces the standard Content–Trigger Alignment check.

### The Five Enforcement Dimensions

| Dimension | What to Look For | Score |
|-----------|-----------------|-------|
| **Scope boundary defined** | Does the skill explicitly state what "counts" as the triggering work? | 0–5 |
| **Mandatory checklist present** | Is there a concrete, numbered checklist of what Claude MUST do? | 0–5 |
| **Success/completion criteria explicit** | How does Claude know when it's done? | 0–5 |
| **Handoff clear** | After completing the checklist, what happens next? | 0–5 |
| **Does NOT over-block** | Would this skill incorrectly block work that shouldn't be blocked? | 0–5 |

### Scoring Rubric per Dimension

**Scope boundary (0–5):**
- 0: "before any task" — no boundary at all
- 2: "before creative work" — vague boundary
- 4: "before any code creation or file writing" — specific enough
- 5: Includes explicit "this does NOT apply to" clause

**Mandatory checklist (0–5):**
- 0: "You should consider..." — suggestion, not mandate
- 2: "Claude should..." — imperative but informal
- 4: Numbered list of MUST-do items, each specific
- 5: Checklist is specific + includes one example per item

**Completion criteria (0–5):**
- 0: No mention of when the enforcement is "done"
- 2: "After completing the checklist, continue" — vague
- 4: Explicit output required (e.g., "output a summary of decisions made")
- 5: Explicit output + verification step (e.g., "verify checklist output before proceeding")

**Handoff (0–5):**
- 0: No handoff mentioned
- 2: "Then move on to the actual task" — vague
- 4: Clear next-step instruction (e.g., "after this, invoke the code-creation skill")
- 5: Handoff includes a signal the next skill can read

**Over-blocking (0–5):**
- 0: Would block clearly unrelated work (e.g., "before any creative work" includes writing an email)
- 2: May occasionally over-block
- 4: Designed to avoid common edge cases
- 5: Includes explicit "do NOT trigger when" conditions

### Example Enforcement Skill (well-scored)

Skill: `brainstorming` — "You MUST use this before any creative work"

| Dimension | Score | Why |
|-----------|-------|-----|
| Scope boundary | 5 | "creative work" is explicitly defined: code, docs, content creation |
| Mandatory checklist | 4 | Has numbered checklist, could add one example per item |
| Completion criteria | 4 | "After this, proceed to create..." — clear signal |
| Handoff | 4 | Explicit next-step instruction |
| Over-blocking | 4 | Email writing excluded; broad enough to catch code+docs |

**Total: 21/25 → 84 → Good**

### Example Enforcement Skill (poorly-scored)

Skill: "Use this before any task"

| Dimension | Score | Why |
|-----------|-------|-----|
| Scope boundary | 0 | "any task" is meaningless — everything is a task |
| Mandatory checklist | 0 | No checklist at all |
| Completion criteria | 0 | No completion criteria |
| Handoff | 0 | No handoff mentioned |
| Over-blocking | 0 | Would block every single user request |

**Total: 0/25 → 0 → Poor**

---

## Proactive Skill Evaluation Path

Proactive skills (trigger mode = Proactive) fire automatically based on context, not user requests. Their description is less about trigger phrases and more about *observable context conditions*.

### The Three Proactive Dimensions

| Dimension | What to Look For | Score |
|-----------|-----------------|-------|
| **Trigger condition is explicit and observable** | Does it specify a concrete context signal (e.g., file changed, error detected)? | 0–10 |
| **Trigger scope is bounded** | Could this fire constantly, or only in specific situations? | 0–10 |
| **Has a "do NOT trigger when" clause** | Are false-positive scenarios explicitly excluded? | 0–5 |

### Scoring Rubric per Dimension

**Trigger condition (0–10):**
- 0: "fires when helpful" — completely unobservable
- 3: "fires when working on a project" — too vague, every session qualifies
- 7: "fires when a test failure is detected in CI output" — specific, observable
- 10: "fires when `pytest` exits non-zero AND the failure is in `tests/unit/`" — maximally specific

**Trigger scope (0–10):**
- 0: No scope limitation — would fire dozens of times per session
- 3: "fires on any error" — broad but not universal
- 7: "fires once per file, after the first error is detected" — self-limiting
- 10: Includes explicit rate-limiting or deduplication logic

**Do NOT trigger when (0–5):**
- 0: No negative condition
- 2: "does not fire for obvious typos" — vague negative
- 5: "does not fire when: the error is a known lint issue, or the user explicitly said 'ignore errors'" — specific exclusions

---

## Common Effectiveness Failure Modes

### Failure Mode 1: The Vague Workflow

**Symptom:** Core workflow contains steps like "understand X", "analyze Y", "implement Z".

**Fix:** Rewrite each step as an imperative that includes a named tool and verification signal.

**Before:** *"Understand the codebase structure."*
**After:** *"Run `ls -R` at the project root. Identify the top-level directories. Read the `package.json` or `Cargo.toml` to confirm the project type."*

### Failure Mode 2: Orphan References

**Symptom:** `references/` directory exists with files, but SKILL.md never mentions them.

**Fix:** Add each orphan file to the "Additional Resources" section with a "load when" condition. If the file isn't useful, delete it.

### Failure Mode 3: Bare Reference Links

**Symptom:** References are listed by filename only, no context about when to load them.

**Fix:** Rewrite each reference to include: (1) what it contains, (2) when to load it.

**Before:** `- references/api.md`
**After:** `- **references/api.md** — Load when the user references a specific API endpoint. Contains request/response schemas for all authenticated endpoints.`

### Failure Mode 4: Content-Trigger Mismatch

**Symptom:** Description promises something the body doesn't deliver.

**Fix:** Either add the missing content to the body, or remove the promise from the description.

### Failure Mode 5: Bloated SKILL.md (>3,000 words)

**Symptom:** SKILL.md is monolithic — no progressive disclosure, all content crammed into one file.

**Fix:** Extract detail sections into `references/` files. Keep SKILL.md to 1,500–2,000 words.

**What to extract:**
- Deep-dive technical details → `references/technical-deep-dive.md`
- Troubleshooting guide → `references/troubleshooting.md`
- Extended examples → `examples/` directory
- Validation scripts → `scripts/` directory
