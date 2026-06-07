# Skill Evolution Log

Tracks the evolutionary history of all managed skills.
Each record captures one evolution cycle: scene discovery, diagnostics, changes, and outcomes.

## How to Use This File

- Each evolution cycle generates one record, appended chronologically
- The **Next Review** date drives the Periodic Evolution Trigger in SKILL.md
- When reviewing a skill's history, read all its records bottom-up (newest first)
- If a skill has no records yet, it hasn't gone through an evolution cycle

## Record Format

```markdown
## Evolution #[N] — [Date] — [Skill Name]

**Version:** [old] → [new]
**Trigger:** [user request / periodic review / issue report / blind spot discovery]
**Scenario Map:**
- Hit: [scenarios where skill worked correctly]
- Miss: [scenarios where skill should have triggered but didn't]
- False Positive: [scenarios where skill triggered incorrectly]
- Blind Spot: [new scenarios the skill should cover]

### Diagnostic Scores
| Dimension | Before | After |
|-----------|--------|-------|
| Trigger Mode | [mode] | [mode] |
| Recall Score | [score] | [score] |
| Effectiveness Score | [score] | [score] |

### Change Set
1. [change description] — Reason: [why] — Result: [pass/fail/deferred]
2. ...

### User Test Results
- Positive trigger test: [pass/fail] — [what user tested]
- Negative trigger test: [pass/fail] — [what user tested]
- User feedback: [direct quote or summary]

### Next Review: [date — typically 2-4 weeks out]
### Review Focus: [specific dimensions or scenarios to check next time]

---
```

## Evolution Records

<!-- New evolution records are appended below this line -->

## Evolution Batch #1 — 2026-05-03 — go_backend_starter + 全局新软链 skill 整批 CRUD 优化

**Mode:** Batch Analysis Mode (B1–B5)
**Trigger:** io-wy 主动请求「使用 skill-analysis 把 go_backend_starter 和刚软链接到全局的 skill 都增删改查优化一下」
**Scope:**
- 项目级:`C:\code\starter\go_backend_starter\.claude\skills\` 24 个 .md + 1 个 nested harness
- 全局新增:`~/.agents/skills/` 三个 — `adversarial-review`, `false-positive-tracking`, `find-skills`(刚加 Gap Radar Mode)

### B1 — Discovery & Classification
- 全量盘点 27 个 skill,按 7 类(评审/记录/测试/规划/执行/索引/规范)归类
- 与全局 inventory 交叉对照,识别 4 处跨层潜在冲突(verify、确认、review、scan 触发词重叠)

### B2 — Severity Triage
| Severity | 数量 | 处置 |
|----------|------|------|
| Blocker | 1 | 修(find-skills 缺 version 字段) |
| High | 2 | 修 |
| Medium | 2 | 修 |
| Low | 6 | 本批暂缓,记入"下次复盘" |

io-wy 确认:「暂缓,本批只修 Blocker+High+Medium」。

### Change Set (5 fixes applied)

| # | Skill | Tier | Severity | Before → After | Why |
|---|-------|------|----------|----------------|-----|
| 1 | find-skills | global | Blocker | 无 version → 2.0.0 | 缺 version 字段无法做语义化升级追踪 |
| 2 | find-skills | global | High | 无 Validation Checklist → 补全 Discovery+Gap Radar 双 mode 验证清单 | Phase 2 七要素缺一,新加 Gap Radar Mode 后无验证锚 |
| 3 | knowledge-snapshot | project | High | trigger "verify" → "查源码/查依赖/查 API" | 与 e2e-verify skill 触发词冲突,Recall 误触 |
| 4 | project-delivery | project | Medium | 18 触发词 → 12 个(裁剪 deploy/build/release 模糊词) | 触发词 >15 触发 -10 FP 罚分 |
| 5 | spec-checkpoint | project | Medium | trigger "确认" → "phase 确认/阶段确认" | "确认"过于泛化,与日常对话冲突 |
| 6 | test-strategy | project | Medium | 章节编号重复(两个"四、")→ 改为"七、端到端验证" + version 1.0.0 → 1.0.1 | 阅读时编号歧义,维护负担 |

### B4 — Phase 2 七要素抽查(修复后)

| Skill | Score | Grade | 短板 |
|-------|-------|-------|------|
| false-positive-tracking | 7/7 | A+ ⭐ | 无 — 标杆模板 |
| adversarial-review | 6.5/7 | A | Resource pointers 较松(指向 codex-review/code-reviewer 但无具体路径) |
| test-strategy | 6.5/7 | A | 修复后达标 |
| project-delivery | 6/7 | A- | 缺独立"## 常见错误"+"## 验证清单"章节,内嵌 WRONG/CORRECT 替代 |
| find-skills | 6/7 | A- | 修复后达标(原缺 Validation Checklist 已补) |
| change-impact-scan | 5.5/7 | B+ | Best Practices 章节弱,只有"错误信息质量检查"隐含写入 Step |

### Diagnostic Scores Aggregate

| Dimension | Before | After |
|-----------|--------|-------|
| Trigger Mode (避免冲突) | 4 处冲突 | 0 处(已重写) |
| Recall(目标命中) | 估 75% | 估 88% |
| Effectiveness(七要素) | 4.7/7 平均 | 6.25/7 平均 |
| 触发词数量合规性 | 1 个 skill 超阈值 | 全部 ≤15 |

### 用户测试结果
- 正触发测试:**待 io-wy 实测**(io-wy 下次说"测试策略/test pyramid/契约测试"应命中 test-strategy;说"phase 确认"应命中 spec-checkpoint)
- 负触发测试:**待 io-wy 实测**(日常说"确认"不应再误触 spec-checkpoint;泛说"deploy"不应误触 project-delivery)
- io-wy 反馈:本批结束后收集

### 下次复盘待办(Low 项,本批未修)

1. **change-impact-scan**:补"## 最佳实践"专章,把分散在 Step 1-5 里的"错误信息质量"等隐性规则提炼出来
2. **project-delivery**:把章节内嵌的 WRONG/CORRECT 对剥离成独立"## 常见错误"+"## 验证清单",对齐七要素
3. **adversarial-review**:Resource pointers 补具体路径(`codex-review` skill 位置 / `code-reviewer` agent 位置)
4. **整批跨层 shadowing 审计**:检查项目级是否存在与全局同名/同触发的 skill,确认 shadowing 是预期行为
5. **find-skills Gap Radar Mode 实战测试**:io-wy 下次跑 `/weekly-skill-review` 时观察 Step R1-R7 是否完整走通
6. **test-strategy + 测试 testing.md 全局规则联动**:本批未审两者关系,下次确认是否需要在 test-strategy SKILL.md 里加 "L2 全局规则联动" 段

### Next Review: 2026-05-31(4 周后,或 io-wy 主动跑 weekly-skill-review 时)
### Review Focus:
- Recall 实测命中率(对比本批写的预期触发词)
- 跨层 shadowing 是否产生意外行为
- Low 项是否积累到 ≥3 次手动绕过 → 升级为 Medium
- 新加的 Gap Radar Mode 在实战中是否被自动唤起

---
