---
name: skill-analysis
description: This skill should be used when the user asks to "analyze a skill", "evaluate skill quality", "check skill recall", "improve skill effectiveness", "audit skill triggers", "skill review", "how is my skill performing", "skill gap analysis", "skill evolution plan", "why is my skill not firing", "fix skill triggers", "skill description review", "this skill fires on wrong requests", "evolve a skill", "skill evolution cycle", "run skill evolution", "time to evolve skills", "which skills need evolution", "batch analyze skills", "polish skills", "empirical verification", "run skill eval", "measure skill recall", or needs to assess whether a skill's description triggers correctly (with optional empirical eval), whether recall rate is good, whether content actually delivers results, whether quality meets best practices, or how to iteratively improve and evolve skills through collaborative user feedback cycles.
version: 0.5.0
---

# Skill Analysis — Evaluate, Diagnose, and Evolve Skills

This skill provides a structured framework for analyzing existing skills across two independent dimensions: **Recall Score** (does the description trigger in the right situations?) and **Effectiveness Score** (does the content deliver results when triggered?). The evaluation path adapts based on the skill's trigger mode.

**Phase 5** adds the **Collaborative Evolution Cycle** — a repeatable loop that combines analysis, user discussion, and iterative improvement into a skill's ongoing evolution.

**Phase 6** (optional) adds **Empirical Verification** — replace论证主义 description审 with subprocess-based evals: train/test split + multi-run voting + LLM self-rewrite, scored by real trigger rates.

> **三句话（读这一段就行）：**
> 1. **该用时召不出，比不召更糟。** 测 `should_trigger=true` 的真实命中率，别只判断描述读起来顺不顺。
> 2. **不该用时硬召，比召不出更糟。** 测 `should_trigger=false` 的反例，别只列正例。
> 3. **改完没测就不算改。** train/test split + 自动重测 + 按 test_passed 选最优——改完看着像就提交是过拟合。

## When to Activate

- Auditing or reviewing existing skills
- Investigating why a skill failed to trigger — or triggered on wrong requests
- Evaluating whether description is too broad, too narrow, or wrong format
- Assessing whether skill content actually guides Claude to good outcomes
- Planning updates to a skill's triggers, content, or structure
- Iterating on a newly created skill after initial usage
- Running a collaborative evolution cycle (analyze → discuss → improve → verify → log)
- Checking which skills are due for periodic evolution review
- Recording evolution history and scheduling next reviews
- Batch-analyzing or polishing multiple skills at once
- Running empirical verification on a skill's description recall (subprocess-based eval)
- Iterating description with auto train/test split + LLM rewrite + retest

## Decision Tree

```
输入分析
├─ 单个 Skill 分析
│   ├─ 触发问题（不触发/误触发）→ Phase 0 + Phase 1 (+ Phase 6 if empirical) → 修 description
│   ├─ 内容问题（触发后效果差）→ Phase 0 + Phase 2 → 修 body
│   ├─ 实证验证 description → Phase 0 + Phase 6 → 出实证证据 + 可选自动改写
│   ├─ 全面对照检查 → Phase 0–4 → 输出 Overall Assessment
│   └─ 不确定问题在哪 → Quick Evolution Mode（Phase 0 + Phase 1 only）
├─ 批量 Skill 分析
│   ├─ Phase 0–1 扫描全部 → 产出 Recall 评分表
│   ├─ 识别 Blocker/High → 优先修复
│   └─ Phase 2 抽查低分 Skill → 产出 Effectiveness 报告
├─ Skill 进化
│   ├─ 新建 Skill → 参考 skill-anatomy.md 构建骨架 → Phase 0–2 验证
│   ├─ 改进现有 Skill → Phase 5 完整进化周期
│   └─ 定期回顾 → Periodic Evolution Trigger
└─ 跨 Skill 冲突
    └─ Phase 3 → 去重/区分/合并建议
```

## Tool Strategy

| 任务 | 首选工具 | 备选 |
|------|---------|------|
| 读取 Skill 文件 | `Read` | — |
| 批量发现 Skill 文件 | `Glob` `**/*.md` | `Bash` (ls) |
| 搜索触发短语 | `Grep` description 字段 | 手工计数 |
| 检查跨 Skill 冲突 | `Grep` trigger phrases | 手工对比 |
| 验证 references/ 文件存在 | `Glob` `references/**` | `Bash` (ls) |
| 读取参考文件 | `Read` `references/*.md` | — |
| 查询最新框架文档 | `mcp__context7__query-docs` | `WebSearch` |
| 修改 Skill 文件 | `Edit` | `Write` (全量重写) |
| 记录进化日志 | `Write` `evolution-log.md` | `Edit` (追加) |

## Analysis Framework

Two scores are produced independently:

- **Recall Score (0–100)** — quality of description as a trigger signal
- **Effectiveness Score (0–100)** — quality of content when triggered

Run phases in order. Phase 0 determines which evaluation path applies.

---

## Phase 0: Trigger Mode Classification

Identify the trigger mode first. The mode changes what "good" looks like.

| Mode | Signal in Description | Evaluation Path |
|------|-----------------------|-----------------|
| **Reactive** | Fires when user explicitly requests something | Full recall scoring (Phases 1–2) |
| **Enforcement** | Mandates Claude behavior before a class of work | Scope clarity + checklist assessment |
| **Proactive** | Auto-fires based on context without explicit request | Trigger condition precision assessment |

**Detection rules:**
- Contains "You MUST / ALWAYS use this before [class of work]" → **Enforcement**
- Contains "Automatically triggers / fires proactively when" → **Proactive**
- Default → **Reactive**

**Output:**
```
**Trigger Mode:** Reactive / Enforcement / Proactive
**Evidence:** "<quote from description>"
```

---

## Phase 1: Description → Recall Analysis

**Objective:** Evaluate how accurately the description selects the right situations to trigger.

### Step 1.1 — Extract Description

Parse the SKILL.md frontmatter and extract the `description` field verbatim.

### Step 1.2 — Format Checks (all modes)

| Check | Criteria | Weight |
|-------|----------|--------|
| Correct signal form | Reactive: "This skill should be used when…" / Enforcement: "You MUST use this before…" / Proactive: "Automatically triggers when…" | Mandatory |
| No parasitic second-person | Does not contain "you should", "you can", "use this when you…" mixed into reactive description | Mandatory |
| Not vague | No generic phrases like "provides guidance", "helps with" without specifics | High |
| Not redundant | Description does not merely restate the skill name | Medium |
| Version field | Has `version: x.x.x` in frontmatter | Low |

Mandatory failures → **Blocker** regardless of mode.

### Step 1.3 — Quantitative Trigger Analysis (Reactive mode only)

**A. Phrase Count**

Count explicit quoted trigger phrases:

| Count | FN Penalty |
|-------|-----------|
| 1 | −25 |
| 2–3 | −15 |
| 4–8 | 0 (ideal) |
| 9–15 | −5 |
| >15 | −10 (FP risk) |

**B. Vocabulary Diversity**

| Axis | Check | Penalty if missing |
|------|-------|--------------------|
| Verb variants | ≥2 synonymous action verbs (create / add / set up / register) | FN −10 |
| Lifecycle coverage | Includes debug/fix/check stages beyond creation | FN −15 |
| Scenario triggers | Includes goal-based phrases ("X not working", "how do I Y") | FN −10 |

**C. Domain Anchoring**

Does the description contain at least one domain-specific proper noun or technical entity (e.g., "Playwright", "PreToolUse hook", "Pulumi ESC")?

| State | FP Penalty |
|-------|-----------|
| No domain anchor — generic verbs only | −15 |
| 1+ domain-specific terms | 0 |

**D. Natural Language Alignment**

| State | Adjustment |
|-------|-----------|
| Technical jargon only (users wouldn't phrase it this way) | FN −10 |
| Mix of jargon and natural phrasing | 0 |
| Primarily natural user phrasing | +5 |

### Step 1.4 — Mode-Specific Assessment (Enforcement / Proactive)

**Enforcement mode — assess:**
- Is the enforcement scope clearly bounded? ("before any creative work" vs "before any task")
- Is the mandatory condition unambiguous?
- Could this over-block unrelated work?
- Is there a clear completion signal ("after this, proceed to X")?

**Proactive mode — assess:**
- Is the auto-trigger condition explicit and observable?
- Is the trigger scope bounded enough to avoid firing constantly?
- Is there a "should NOT trigger when" clause?

### Step 1.5 — Recall Score Computation

```
Recall Score = 100 − (FN penalties from 1.3) − (FP penalties from 1.3)
Floor: 0  |  Ceiling: 105 (natural language bonus)
```

| Score | Rating |
|-------|--------|
| 85–100 | Excellent |
| 70–84 | Good |
| 50–69 | Needs Improvement |
| 0–49 | Poor |

For Enforcement/Proactive: output qualitative assessment, not a numeric score.

### Step 1.6 — Output Phase 1

```
## Phase 1: Description → Recall Analysis

**Trigger Mode:** <Reactive / Enforcement / Proactive>

### Format Checks
| Check | Result |
|-------|--------|
| Correct signal form | PASS / FAIL |
| No parasitic second-person | PASS / FAIL |
| Not vague | PASS / FAIL |
| Version field | PASS / FAIL |

### Quantitative Analysis (Reactive)
| Dimension | Finding | Penalty |
|-----------|---------|---------|
| Phrase count | <n> phrases | <−n> |
| Verb variants | <list> | <−n or 0> |
| Lifecycle coverage | <stages covered> | <−n or 0> |
| Domain anchor | <term or "none"> | <−n or 0> |
| Natural language | <assessment> | <−n, 0, or +5> |

**Recall Score:** <0–100> (<Excellent/Good/Needs Improvement/Poor>)
— OR for Enforcement/Proactive: **Assessment:** <qualitative>

**Recommended trigger changes:** <list or "None">
```

---

## Phase 2: Content → Effectiveness Analysis

**Objective:** Evaluate whether the skill body actually guides Claude to good outcomes when triggered.

### Step 2.1 — SKILL.md Body Metrics

**Word count** (excluding frontmatter):

| Range | Rating |
|-------|--------|
| 1,500–2,000 words | Ideal |
| <3,000 words | Acceptable |
| 3,000–5,000 words | Overweight |
| >5,000 words | Bloated — no progressive disclosure used |

**Writing style:** Sample 5–10 paragraphs. Flag second-person errors ("You should…", "You can…").

### Step 2.2 — Workflow Actionability Score (0–25)

Sample the core workflow steps. Score each step:

| Score | Criteria |
|-------|----------|
| 0 | Vague: "analyze the requirements", "implement the feature" |
| 1 | Specific but incomplete: action stated, no tool/command/verification |
| 2 | Fully actionable: imperative verb + named tool or command + how to verify |

`Sub-score = (sum / max_possible) × 25`

A step scoring 2 looks like: *"Run `python scripts/discover.py --json`. Read `runner.framework` field. If missing, stop and report blocked."*
A step scoring 0 looks like: *"Understand the repository structure."*

### Step 2.3 — Progressive Disclosure Quality (0–25)

For each file in `references/`, `examples/`, `scripts/`:

| Condition | Points |
|-----------|--------|
| File exists AND is referenced in SKILL.md | +3 |
| Reference includes explicit "load when" / "use for" condition | +4 |
| File has sufficient depth (references/ ≥ 500 words) | +3 |

Cap at 25. Flag:
- **Orphan files** — exist but not referenced
- **Missing links** — referenced but file doesn't exist
- **Bare references** — listed but no "load when" condition (Claude won't know when to load)

### Step 2.4 — Content–Trigger Alignment (0–25)

Cross-check: for each trigger scenario promised in the description, does the SKILL.md body actually address it?

| Gap type | Penalty |
|----------|---------|
| Major gap: description promises X, body has nothing on X | −15 |
| Partial gap: coverage exists but too shallow to be useful | −7 |

`Sub-score = 25 − total_penalties` (floor 0)

### Step 2.5 — Enforcement Skill Special Assessment (replaces 2.4 if mode = Enforcement)

| Check | Score |
|-------|-------|
| Scope boundary defined (what exactly counts as "creative work"?) | 0–5 |
| Mandatory checklist present and specific | 0–5 |
| Success/completion criteria explicit | 0–5 |
| Handoff clear ("after completing this, proceed to X") | 0–5 |
| Does NOT over-block clearly unrelated work | 0–5 |

`Sub-score = total / 25`

### Step 2.6 — Content Completeness (0–25)

| Element | Score |
|---------|-------|
| Purpose statement (1–2 sentences) | 0–2 |
| When to activate (explicit list) | 0–2 |
| Core workflow (step-by-step) | 0–2 |
| Resource pointers (references/examples/scripts) | 0–2 |
| Best practices (domain-specific do's/don'ts) | 0–2 |
| Common mistakes (3–5 pitfalls with corrections) | 0–2 |
| Validation checklist (how to verify success) | 0–2 |

`Sub-score = (sum / 14) × 25`

### Step 2.7 — Effectiveness Score

```
Effectiveness Score = Workflow (0–25) + Progressive Disclosure (0–25)
                    + Alignment (0–25) + Completeness (0–25)
```

| Score | Rating |
|-------|--------|
| 85–100 | Excellent |
| 70–84 | Good |
| 50–69 | Needs Improvement |
| 0–49 | Poor |

### Step 2.8 — Output Phase 2

```
## Phase 2: Content → Effectiveness Analysis

**SKILL.md:** <word-count> words (<ideal/acceptable/overweight/bloated>)
**Second-person errors:** <n violations>

### Workflow Actionability
| Step | Score | Issue |
|------|-------|-------|
| <step summary> | /2 | <note or —> |
**Sub-score:** <n>/25

### Progressive Disclosure Quality
| File | Referenced | Load-When Condition | Depth |
|------|-----------|---------------------|-------|
| references/<file> | YES/NO | YES/NO | OK/Thin |
**Orphan files:** <list or "None">
**Missing links:** <list or "None">
**Sub-score:** <n>/25

### Content–Trigger Alignment
**Gaps found:** <list or "None">
**Sub-score:** <n>/25

### Content Completeness
| Element | Score |
|---------|-------|
| Purpose statement | /2 |
| Activation triggers | /2 |
| Core workflow | /2 |
| Resource pointers | /2 |
| Best practices | /2 |
| Common mistakes | /2 |
| Validation checklist | /2 |
**Sub-score:** <n>/25

**Effectiveness Score:** <0–100> (<rating>)
```

---

## Phase 3: Cross-Skill Conflict Check

List sibling skills in the same directory. For each, check whether trigger phrases overlap with the skill under analysis.

| Conflicting Skill | Overlapping Triggers | Risk Level |
|-------------------|---------------------|------------|
| <skill-X> | "<phrase A>", "<phrase B>" | High / Medium / Low |

**Recommendation:** Disambiguate / Merge / Keep separate with context

---

## Phase 4: Evolution Planning

Triage all findings from Phases 1–3:

| Severity | Definition | Action |
|----------|------------|--------|
| **Blocker** | Mandatory format failure, or trigger mode misclassified | Fix immediately |
| **High** | Recall Score <70, or Effectiveness Score <70, or conflict detected | Fix within 1 iteration |
| **Medium** | Either score 70–79, or content completeness gaps | Fix within 2 iterations |
| **Low** | Style violations, orphan files, bare references | Fix when convenient |

For each issue:
```
**[SEVERITY]** <issue description>
- Evidence: <quote or measurement>
- Action: <specific change>
```

Output a prioritized roadmap (blockers → high → medium → low, quick wins first within tier).

---

## Batch Analysis Mode

When the user asks to "batch analyze", "polish all skills", or provides a directory of skills:

### Step B1 — Discover & Classify

1. `Glob` all `*.md` files in the skill directory
2. For each file, extract frontmatter (Read first 10 lines)
3. Classify trigger mode (Phase 0) and check format (Phase 1.2)
4. Output a compact table:

```
## Batch Phase 0–1 Scan

| # | Skill | Mode | Version | Frontmatter | Recall Est. |
|---|-------|------|---------|-------------|-------------|
| 1 | skill-name | Reactive/Enforcement/Proactive | ✅/❌ | ✅/❌/MISSING | Good/Needs Fix/Blocker |
```

### Step B2 — Prioritize by Severity

| Severity | Detection | Action |
|----------|-----------|--------|
| **Blocker** | No frontmatter / no version | Fix immediately (add standard frontmatter) |
| **High** | Recall < 70 / missing trigger phrases | Fix description within this batch |
| **Medium** | Missing common mistakes / validation checklist | Fix content within this batch |
| **Low** | Style / naming / minor issues | Log for later |

### Step B3 — Execute Fixes

1. Fix all Blockers first (parallel if independent)
2. Fix all High issues (description improvements)
3. Fix Medium issues selectively
4. Output summary table of all changes made

### Step B4 — Phase 2 Spot Check

For skills that scored Good+ on Recall but might have content gaps:
1. Quick scan body for 7 content completeness elements
2. Flag skills missing 3+ elements
3. Propose targeted content additions

---

## Analysis Constraints

1. **Read before judging** — Never score a skill without reading the full file. Summaries from filenames alone are guesses, not assessments.
2. **Score independently** — Recall and Effectiveness are separate dimensions. A skill with excellent triggers can have terrible content, and vice versa.
3. **Prefer user ground truth** — If diagnostics say "fix X" but the user says "X works fine in practice", trust the user. They have production data you don't.
4. **No drive-by criticism** — Every issue flagged must include a specific, actionable fix. "Description is bad" is useless. "Add 3–5 trigger phrases covering debug/fix scenarios" is actionable.
5. **Batch efficiency** — When analyzing 10+ skills, group common issues and propose batch fixes rather than per-skill micro-optimizations.
6. **Verify before reporting** — Re-read modified files to confirm changes applied correctly before declaring victory.

---

## Reference Speed-cheat

### Description Quality Checklist (Quick)

| Check | PASS if | FAIL if |
|-------|---------|---------|
| Frontmatter exists | Has `---` + name + description + version | Missing any field |
| Trigger mode clear | Says "Triggered when" / "You MUST" / "Automatically" | No trigger signal |
| 4–8 trigger phrases | Count quoted phrases in description | <4 or >15 |
| Domain anchor | Contains ≥1 domain-specific noun | Only generic verbs |
| Verb diversity | ≥2 synonymous action verbs | Only 1 verb pattern |
| Not vague | Specific about what the skill does | "Provides guidance" / "Helps with" |

### Content Completeness Quick Scan

| Element | Look for | Score |
|---------|-----------|-------|
| Purpose | `> 核心：` or 1–2 sentence intro | /2 |
| Triggers | `## 触发条件` or `## When to Activate` | /2 |
| Workflow | `### Step` / `### Phase` numbered steps | /2 |
| Best practices | `常见错误` / `Constraints` table | /2 |
| Mistakes | 3–5 items with consequence + prevention | /2 |
| Checklist | `验证清单` / `Validation` checkbox list | /2 |

### Common Skill Anti-patterns

| Anti-pattern | Symptom | Fix |
|-------------|---------|-----|
| **Ghost skill** | No frontmatter → Claude can't discover it | Add `---` block with name/description/version |
| **All-phases-no-routing** | Flat list of steps, no decision branches | Add Decision Tree for scenario routing |
| **Description as docstring** | Description explains internal design, not when to use | Rewrite: "Triggered when [scenario], covers [scope]" |
| **Monolith skill** | >3000 words, no progressive disclosure | Extract deep content to `references/` |
| **Trigger phrase desert** | Only skill name as trigger | Add 4–8 diverse phrases (verbs + scenarios + goal-based) |
| **Orphan checklist** | Has validation checklist but items don't match workflow | Align checklist items with actual workflow steps |

### Frontmatter Template by Mode

**Reactive:**
```yaml
---
name: skill-name
version: 1.0.0
description: <1-2 sentences: what it does>. Triggered when <scenario>, or user says "<trigger phrases>".
---
```

**Enforcement:**
```yaml
---
name: skill-name
version: 1.0.0
description: <1-2 sentences: what it mandates>. You MUST use this before <scope> — <what it ensures>. Triggered when <scope condition detected>.
---
```

**Proactive:**
```yaml
---
name: skill-name
version: 1.0.0
description: <1-2 sentences: what it auto-does>. Automatically triggers when <observable condition>. Does NOT trigger when <exclusion>.
---
```

---

## Phase 5: Collaborative Evolution Cycle

**Objective:** Iteratively improve a skill through a structured loop of scene discovery, diagnosis, user discussion, improvement, and verification. This is the engine that keeps skills alive and effective over time.

### Evolution Cycle Flow

```
Scene Discovery → Diagnostic Assessment → User Discussion → Improve → Verify → Log → (schedule next review)
```

The cycle can be initiated by:
1. User explicitly asks to "evolve skill X"
2. Phase 4 analysis reveals issues that warrant deeper iteration
3. Periodic evolution review is due (check `references/evolution-log.md`)
4. User reports a skill problem in conversation

### Step 5.1 — Scene Discovery

Goal: Map the skill's real-world usage landscape through user conversation.

Ask the user these questions (adapt to context, do not ask all at once):

1. "Describe 2–3 recent times you expected this skill to trigger. What actually happened?"
2. "Are there scenarios where this skill fires but shouldn't?"
3. "Are there scenarios where you wanted this skill but it didn't fire?"
4. "Any new use cases that the skill should now cover?"

Synthesize findings into a **Scenario Map**:

| Category | Definition |
|----------|------------|
| **Hit** | Skill triggered correctly, delivered good results |
| **Miss** | Skill should have triggered but didn't (false negative) |
| **False Positive** | Skill triggered incorrectly (false positive) |
| **Blind Spot** | New scenarios the skill should cover but currently doesn't |

Output: Scenario Map, appended to `references/evolution-log.md` under this cycle's record.

### Step 5.2 — Run Diagnostic (Phase 0–4)

Execute Phases 0–4 of this skill's analysis framework on the target skill. This produces:
- Recall Score
- Effectiveness Score
- Conflict check results
- Prioritized issue roadmap

If the user wants a lighter-touch review, run only Phase 0 (trigger mode) + Phase 1 (recall) and skip to Step 5.3.

### Step 5.3 — User Discussion & Change Agreement

Goal: Collaborate with the user to decide what to change and how.

**Presentation format:**
```
## Evolution Discussion — [Skill Name]

### Current State
| Dimension | Score | Rating |
|-----------|-------|--------|
| Recall | [score] | [rating] |
| Effectiveness | [score] | [rating] |

### Scenario Map Summary
- Hit: [count] scenarios
- Miss: [count] scenarios — [list]
- False Positive: [count] — [list]
- Blind Spot: [count] — [list]

### Proposed Changes (by priority)
**P0 — Blockers:**
1. [issue] → Fix: [proposed change]

**P1 — High:**
1. [issue] → Fix: [proposed change]
   Option A: [approach]
   Option B: [approach]

**P2 — Medium:**
1. [issue] → Fix: [proposed change]

**P3 — Low:**
1. [issue] → Fix: [proposed change]
```

**Discussion rules:**
- For P0 issues: propose fix and apply immediately (not negotiable)
- For P1 issues: present 2 options, ask user to choose or suggest alternative
- For P2/P3 issues: propose fix, ask user to confirm or reject
- Listen to user feedback. If user proposes a different approach than what diagnostics suggest, prefer the user's approach — they have ground truth

**Output:** Agreed **Change Set** — list of specific modifications with rationale.

### Step 5.4 — Apply Changes & Verify

Apply each change from the Change Set:

1. **Apply** the change to the skill files
2. **Quick verify** after each change:
   - Re-read the modified file
   - Confirm no regression in other dimensions
   - Confirm trigger phrases still match intended scenarios
3. **Full verify** after all changes:
   - Re-run Phase 0–2 on the updated skill
   - Confirm all targeted issues are resolved
   - Confirm no new issues introduced
4. **User test:**
   - Ask user: "Try asking something that should trigger this skill now"
   - Ask user: "Try asking something that should NOT trigger this skill"
   - Record user's test results

If verification fails, loop back to Step 5.3 for the specific failing item.

### Step 5.5 — Log Evolution Record

Append to `references/evolution-log.md`:

```markdown
## Evolution #[N] — [Date] — [Skill Name]

**Version:** [old] → [new]
**Trigger:** [what prompted this cycle — user request / periodic review / issue report]
**Scenario Map:**
- Hit: [scenarios]
- Miss: [scenarios]
- False Positive: [scenarios]
- Blind Spot: [scenarios]

### Diagnostic Scores
| Dimension | Before | After |
|-----------|--------|-------|
| Recall | [score] | [score] |
| Effectiveness | [score] | [score] |

### Change Set
1. [change description] — Reason: [why] — Result: [pass/fail]
2. ...

### User Test Results
- Positive trigger test: [pass/fail]
- Negative trigger test: [pass/fail]
- User feedback: [quote or summary]

### Next Review: [date — typically 2-4 weeks]
### Review Focus: [what to check next time — specific dimensions or scenarios]

---
```

Update the skill's `version` field in SKILL.md frontmatter according to evolution-guide.md semver rules.

---

## Phase 6: Empirical Verification (Optional)

**Objective:** Replace论证主义 description审 (Phase 1.3 quantitative penalties) with实证 measurement. Run subprocess-based eval on the description against a labeled query set, then optionally iterate via train/test split + LLM self-rewrite.

> **Foundational rule:** When Phase 1论证 conflicts with Phase 6实证, **实证 wins**. The penalty rules in Phase 1.3 are heuristics — Phase 6 measures actual trigger behavior.

### When to activate Phase 6

Activate when **any** of:
- User explicitly requests "empirical verification" / "run skill eval" / "measure recall" / "实证验证"
- Phase 1 论证 result confidence is low (e.g., Reactive mode but trigger phrases ambiguous, or score is borderline 65–75)
- Phase 5 evolution cycle reaches Step 5.4 with description rewrite proposed — empirical proof needed before merge
- io-wy needs to choose between 2+ candidate descriptions

Skip when:
- Quick scan / read-only audit (Phase 6 costs ~$3 + 5–15 min)
- Skill is Enforcement or Proactive mode (Phase 6 is recall-focused, less applicable)
- Cost budget tight or no Anthropic API access available

### Sub-phases (overview)

| Sub-phase | Action | Output |
|-----------|--------|--------|
| **6a** Draft eval set | Compose 16–20 queries: 8–12 `should_trigger=true` + 8–10 `should_trigger=false` | `docs-tmp/analysis/<skill>-eval-set-<date>.json` |
| **6b** Stratified split | Train/test 60/40 split, stratified by `should_trigger`, seed=42 | In-memory `train_set` + `test_set` |
| **6c** Baseline eval | Run eval on current description, `runs_per_query=3` multi-vote at `threshold=0.5` | `baseline_results.json` |
| **6d** Iterate (optional) | LLM rewrites description from `train_results` + blinded history; re-test up to N rounds | `history.json` + `best_description` |
| **6e** Report | HTML auto-refresh report + Markdown summary; results回灌 Phase 1/Phase 5 | `<skill>-eval-<date>.html` + `<skill>-eval-summary.md` |

### Implementation

- Step-by-step procedure: `references/empirical-verification.md`
- Query draft templates: `references/eval-prompt-library.md`
- Scripts: `scripts/run_eval.py` (Anthropic SDK + threading-based stream reader, Windows-safe), `scripts/run_loop.py` (orchestrator), `scripts/improve_description.py` (LLM rewriter), `scripts/generate_report.py` (HTML history report, auto-refresh), `scripts/render_eval_review.py` (populate eval-set review HTML), `scripts/sanity_check.py` (SDK trigger-detection diagnostic), `scripts/utils.py` + `scripts/quick_validate.py` (helpers)
- Assets: `assets/eval_review.html` (browser UI for editing eval set before run_loop)
- Endpoint setup: `make_client()` in `scripts/utils.py` honors `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` + optional `ANTHROPIC_BASE_URL` (Kimi proxy / Bedrock / etc.). Run `python -m scripts.sanity_check` after switching endpoints to recalibrate.

### Cost & duration guardrails

- Per Phase 6 full cycle (16 queries × 3 runs × 1–10 iterations): ~5–15 min, ~$3 USD via Anthropic SDK
- **Always print cost estimate before starting**; require io-wy explicit confirmation when estimated > $5
- max_iterations defaults to 5; cap at 10

### Output integration

- **Into Phase 1:** When Phase 6 disagrees with Phase 1.3 quantitative penalties, output both scores in the report and explicitly mark "Empirical wins" with the conflict reason
- **Into Phase 5.4:** When Phase 5 proposes a description rewrite, run Phase 6d; the `best_description` (selected by max `test_passed`) becomes the change set's description target — replacing the LLM's first-draft rewrite
- **Into evolution-log:** Append the Phase 6 summary table (baseline vs best, train/test pass rates) to that cycle's evolution record

### Phase 6 Output Template

```
## Phase 6: Empirical Verification

**Eval set:** <N> queries (<n_pos> positive + <n_neg> negative)
**Split:** train=<N_train>, test=<N_test> (seed=42)
**Iterations run:** <K> / max=<max>
**Cost actual:** $<X> | Duration: <Y>min

### Per-query results (test set)
| Query | should_trigger | trigger_rate | pass |
|-------|---------------|--------------|------|
| ...   | true          | 3/3 (1.0)    | ✓    |
| ...   | false         | 0/3 (0.0)    | ✓    |

### Iteration history
| Iter | train_passed | test_passed | description |
|------|-------------:|-------------:|-------------|
| 0 (baseline) | 8/12 | 5/8 | "Original..." |
| 1 | 11/12 | 7/8 | "Improved..." |
| 2 (best) | 12/12 | 8/8 | "..." |

**Selected description:** Iteration <K> (test_passed=<X>/<Y>)
**Recall delta:** baseline → final: <Δ>

### Conflicts with Phase 1论证
- <conflict description> — Empirical wins because <reason>
```

---

## Periodic Evolution Trigger

When the user asks to "run skill evolution", "which skills need evolution", or "time to evolve skills":

1. Read `references/evolution-log.md`
2. Check each tracked skill's **Next Review** date
3. Report status:
   ```
   ## Skill Evolution Status

   | Skill | Version | Last Review | Next Review | Status |
   |-------|---------|-------------|-------------|--------|
   | [name] | [ver] | [date] | [date] | Due / On Schedule |
   ```
4. For skills past their review date, propose starting a new evolution cycle
5. For skills not yet due, ask: "Skip, or force an early review?"
6. If no skills are tracked yet, ask: "Which skill should we start tracking?"

When no evolution-log.md exists, create it with the header:
```markdown
# Skill Evolution Log

Tracks the evolutionary history of all managed skills.
Each record captures one evolution cycle.

<!-- New evolution records are appended below -->
```

---

## Quick Evolution Mode

When the user wants a fast check without the full cycle:

1. Read the target skill's SKILL.md
2. Run Phase 0 (trigger mode) + Phase 1 (recall) only
3. Present condensed report:
   - Trigger mode + Recall score
   - Top 3 issues by priority
   - One-sentence suggestion: "Start a full evolution cycle?" or "Quick fix: [specific change]"

## Interactive Evolution Mode

When the user wants to brainstorm skill improvements informally:

1. Ask: "What's bothering you about this skill?"
2. Listen, identify which diagnostic dimensions are affected
3. Propose targeted improvements
4. Ask: "Apply now, or log for a planned evolution cycle?"

---

## Overall Assessment Template

```
## Overall Assessment

| Dimension | Score | Rating |
|-----------|-------|--------|
| Recall Score (Description) | <0–100> | <Excellent/Good/Needs Improvement/Poor> |
| Effectiveness Score (Content) | <0–100> | <...> |
| **Overall Skill Health** | **<avg>** | **<...>** |

### Key Strengths
- <bullet of what works well>

### Critical Gaps
- <bullet of what needs urgent attention>

### Next Step
<One specific immediate action>
```

---

## Reference Files

### `references/evolution-log.md`
Evolution history and scheduled reviews for all managed skills. Load when checking which skills are due for periodic evolution, when starting a new evolution cycle, or when reviewing past evolution records. Contains one record per evolution cycle with before/after scores, change sets, user test results, and next review dates.

### `references/skill-anatomy.md`
Anatomy of a well-formed skill — SKILL.md structure, annotated good/bad description examples, progressive disclosure patterns (Minimal/Standard/Complex), and structural anti-patterns.

### `references/trigger-patterns.md`
Trigger phrase pattern catalog — specificity spectrum, FP/FN mitigation strategies, lifecycle coverage examples, cross-skill disambiguation. Load when diagnosing recall issues or designing new triggers.

### `references/evolution-guide.md`
Skill lifecycle and evolution — semantic versioning, iteration loop (Observe→Diagnose→Act→Validate), breaking changes policy, trigger evolution strategies, skill health metrics table.

### `references/effectiveness-guide.md`
Detailed rubrics for content effectiveness — workflow actionability scoring examples (score 0/1/2 annotated), progressive disclosure quality with "load when" patterns, content–trigger alignment checklist, enforcement skill evaluation path, proactive skill evaluation path. Load when scoring Phase 2 or debugging why a triggered skill gives poor results.

### `references/empirical-verification.md`
Phase 6 detailed procedure — sub-phases 6a–6e step-by-step, decision criteria for activation, Anthropic SDK setup, threading-based stream reader (Windows-safe alternative to `select.select`), cost guardrails, common pitfalls, output schema reference. Load when running Phase 6 or troubleshooting empirical eval failures.

### `references/eval-prompt-library.md`
LLM prompt templates for drafting eval query sets — patterns for `should_trigger=true` queries (明显/边界/lifecycle 三类) and `should_trigger=false` queries (近义/远义/parasitic 三类). Includes worked examples for each Trigger Mode (Reactive/Enforcement/Proactive). Load when starting Phase 6 sub-phase 6a or curating a test eval set.

### `scripts/`
Phase 6 implementation. Key files:
- `utils.py` — SKILL.md frontmatter parser (`parse_skill_md`) + `make_client()` helper (resolves API key from `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN`, honors `ANTHROPIC_BASE_URL` for proxy endpoints)
- `quick_validate.py` — SKILL.md compliance check (frontmatter shape, name kebab-case, description ≤1024 chars)
- `sanity_check.py` — SDK trigger-detection diagnostic (validates the simulated `available_skills` mechanism on the active endpoint; run after switching `ANTHROPIC_BASE_URL`)
- `run_eval.py` — Single-description eval runner (Anthropic SDK + threading, Windows-safe)
- `run_loop.py` — Multi-iteration optimization orchestrator (train/test split + blinded history; writes `baseline_results.json`, `iter_<N>_results.json`, `history.json`, `best_description.txt`)
- `improve_description.py` — LLM-driven description rewriter (uses train results + blinded history)
- `generate_report.py` — HTML history report renderer (rows = iterations, columns = queries, best row highlighted, optional 5s auto-refresh)
- `render_eval_review.py` — Populates `assets/eval_review.html` placeholders (`__SKILL_NAME_PLACEHOLDER__`, `__SKILL_DESCRIPTION_PLACEHOLDER__`, `__EVAL_DATA_PLACEHOLDER__`) so io-wy can audit/edit the eval set in a browser before launching `run_loop`

### `assets/`
Browser-side UI assets for Phase 6:
- `eval_review.html` — Self-contained eval-set review page (no server required). Edits queries inline, toggles `should_trigger`, picks category from `obvious / boundary / lifecycle` (positive) or `near-miss / far-miss / parasitic` (negative), exports a clean `eval_set.json` via client-side download. Populated via `scripts/render_eval_review.py`.
