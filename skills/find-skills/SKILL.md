---
name: find-skills
version: 2.0.0
description: Discover, install, and audit agent skills. Two modes - Discovery (user asks "how do I do X", "find a skill for X", "is there a skill for X", or wants to extend capabilities) and Gap Radar (user says "what skills am I missing", "scan for blind spots", "skill coverage gap", "skill audit", "do I have a skill for X", "weekly skill review", or after 3+ similar manual tasks).
---

# Find Skills

This skill operates in two modes:

- **Discovery Mode** — search and install skills from the open ecosystem when the user has a known need
- **Gap Radar Mode** — proactively scan the user's installed-skill inventory for blind spots, identify capabilities they repeatedly handle manually, and propose targeted skill additions

Both modes share the same install pipeline.

## When to Use This Skill

### Discovery Mode triggers

Use this skill when the user:

- Asks "how do I do X" where X might be a common task with an existing skill
- Says "find a skill for X" or "is there a skill for X"
- Asks "can you do X" where X is a specialized capability
- Expresses interest in extending agent capabilities
- Wants to search for tools, templates, or workflows
- Mentions they wish they had help with a specific domain (design, testing, deployment, etc.)

### Gap Radar Mode triggers

Use this skill when the user:

- Says "what skills am I missing", "scan for blind spots", "skill coverage gap", "skill audit"
- Says "do I have a skill for X" / "is X covered" (single-skill check, often a precursor to weekly review)
- Runs `/weekly-skill-review` or asks for periodic skill review
- Asks "are there skills I should consider"
- Has performed the **same manual task ≥ 3 times** in recent sessions (proactive trigger — suggest scanning even if user didn't ask)
- Has just adopted a new tool/framework/domain → likely has skill gaps in that area

## What is the Skills CLI?

The Skills CLI (`npx skills`) is the package manager for the open agent skills ecosystem. Skills are modular packages that extend agent capabilities with specialized knowledge, workflows, and tools.

**Key commands:**

- `npx skills find [query]` - Search for skills interactively or by keyword
- `npx skills add <package>` - Install a skill from GitHub or other sources
- `npx skills check` - Check for skill updates
- `npx skills update` - Update all installed skills

**Browse skills at:** https://skills.sh/

## Discovery Mode Workflow

> 当用户主动说"找个 skill 来 X"时，本节是主流程。

### Step D1: Understand What They Need

When a user asks for help with something, identify:

1. The domain (e.g., React, testing, design, deployment)
2. The specific task (e.g., writing tests, creating animations, reviewing PRs)
3. Whether this is a common enough task that a skill likely exists

### Step D2: Search for Skills

Run the find command with a relevant query:

```bash
npx skills find [query]
```

For example:

- User asks "how do I make my React app faster?" → `npx skills find react performance`
- User asks "can you help me with PR reviews?" → `npx skills find pr review`
- User asks "I need to create a changelog" → `npx skills find changelog`

The command will return results like:

```
Install with npx skills add <owner/repo@skill>

vercel-labs/agent-skills@vercel-react-best-practices
└ https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices
```

### Step D3: Present Options to the User

When you find relevant skills, present them to the user with:

1. The skill name and what it does
2. The install command they can run
3. A link to learn more at skills.sh

Example response:

```
I found a skill that might help! The "vercel-react-best-practices" skill provides
React and Next.js performance optimization guidelines from Vercel Engineering.

To install it:
npx skills add vercel-labs/agent-skills@vercel-react-best-practices

Learn more: https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices
```

### Step D4: Offer to Install

If the user wants to proceed, you can install the skill for them:

```bash
npx skills add <owner/repo@skill> -g -y
```

The `-g` flag installs globally (user-level) and `-y` skips confirmation prompts.

## Gap Radar Mode

> 当用户问"我还差什么 skill"时，本节是主流程。

雷达扫描的目标：找出用户**正在反复手动做的事**，但 inventory 里没有对应 skill 来自动化。

### Step R1：盘点已装 skill 库存

读取下列位置，列出当前可用 skill 的 `name + description` 一行摘要：

```bash
# 全局源（个人级）
ls ~/.agents/skills/
# 全局符号链接层（curated）
ls ~/.claude/skills/
# 项目级
ls <project>/.claude/skills/
# 项目级 commands（slash 命令也算扩展能力）
ls <project>/.claude/commands/
ls ~/.claude/commands/
```

也可直接用 system reminder 里 `following skills are available for use with the Skill tool` 给的清单（更准确，已包含 description）。

### Step R2：识别"反复手动做的事"

**输入信号**（按优先级）：

1. **用户主动说**："我每周都要 X" / "上次我也是这么改的" / "又是 X 这一套" → 高置信度信号
2. **最近会话痕迹**：扫描 evolution-log、PIT 日志、最近 N 个任务的主题，找重复
3. **当前任务类型**：用户发起的本次任务，看 inventory 是否覆盖
4. **新引入的领域/工具**：用户刚开始用某新框架/平台 → 那领域大概率没 skill

把"反复做的事"列成清单：

```
- 重复主题 / 触发频次 / 当前是手动还是 skill / 候选 skill 名
```

### Step R3：交叉对照——找盲区

对每个重复主题，做三类判定：

| 判定 | 定义 | 处理 |
|------|------|------|
| **已覆盖** | inventory 里有对应 skill 且描述匹配 | 提示用户该 skill 存在但可能没主动触发，建议加触发关键词到 SKILL.md description |
| **部分覆盖** | 有相关 skill 但只解决一部分 | 建议扩展该 skill，或并装一个互补 skill |
| **未覆盖** | inventory 完全没有对应能力 | 走 Step R4 找候选；找不到走 Step R5 自建 |

### Step R4：搜索候选 skill

对未覆盖的盲区，按下列顺序搜：

```bash
# 1. 开放生态（npx skills）
npx skills find <gap-keyword>

# 2. 已知高质量源（Vercel / Composio / Anthropic 官方）
npx skills find vercel-labs <keyword>
npx skills find anthropic <keyword>

# 3. 通过通用搜索引擎找 GitHub repo
# WebSearch: "agent skill <keyword> SKILL.md"
```

筛选标准：
- description 必须命中盲区的核心动词
- 维护活跃（近 6 个月有 commit）
- 触发关键词覆盖用户的常用表述

### Step R5：自建 skill 的判定

走到这一步说明开放生态没有现成的。判定要不要自建：

| 条件 | 自建？ |
|------|--------|
| 频次 ≥ 3 次/月 且步骤稳定 | ✅ 用 `skill-creator` 启动 eval-driven 创建流程 |
| 频次 < 3 次/月 但每次步骤复杂 | ⚠️ 先记到 `skill-analysis` 的 evolution-log，攒到稳定后再建 |
| 步骤不稳定/每次都不一样 | ❌ 不适合自动化，跳过 |
| 涉及强项目特定上下文 | 项目级 skill（不入全局） |

### Step R6：输出雷达报告

```markdown
# Skill Gap Radar Report — YYYY-MM-DD

## 已盘点 inventory
- 全局: N 个 skill (列出 top 10 + 数量)
- 项目级: M 个 skill
- Commands: K 个

## 重复手动做的事（候选 gap）
| 主题 | 频次 | 当前处理 | 判定 |
|------|------|---------|------|
| ... | 每周 2 次 | 手动写 | 未覆盖 |
| ... | 每月 1 次 | adversarial-review | 已覆盖 |

## 推荐安装（开放生态命中）
1. `<owner/repo@skill>` —— 解决 <gap>，install: `npx skills add ... -g -y`
2. ...

## 推荐自建（生态无命中）
1. `<proposed-name>` —— 解决 <gap>，建议用 skill-creator 启动 eval 闭环
2. ...

## 建议增强现有 skill
1. `<existing-skill>` —— 加触发关键词 "<phrase>" 到 description，提升召回
2. ...

## 下次复盘
- 建议时间: 1 周后 / 完成本次推荐项后
- 重点观察: 新装/自建 skill 的实际触发频次
```

### Step R7：与 evolution-log 联动

雷达报告完成后：

- 把 `推荐自建` 项追加到 `~/.agents/skills/skill-analysis/references/evolution-log.md` 的待办区
- 已采纳的安装/增强项，下周复盘时回看效果（命中率、误触发、未触发）
- 形成 **雷达 → 选 → 装/建 → 用 → 复盘 → 雷达** 的闭环

## Common Skill Categories

When searching, consider these common categories:

| Category        | Example Queries                          |
| --------------- | ---------------------------------------- |
| Web Development | react, nextjs, typescript, css, tailwind |
| Testing         | testing, jest, playwright, e2e           |
| DevOps          | deploy, docker, kubernetes, ci-cd        |
| Documentation   | docs, readme, changelog, api-docs        |
| Code Quality    | review, lint, refactor, best-practices   |
| Design          | ui, ux, design-system, accessibility     |
| Productivity    | workflow, automation, git                |

## Tips for Effective Searches

1. **Use specific keywords**: "react testing" is better than just "testing"
2. **Try alternative terms**: If "deploy" doesn't work, try "deployment" or "ci-cd"
3. **Check popular sources**: Many skills come from `vercel-labs/agent-skills` or `ComposioHQ/awesome-claude-skills`

## When No Skills Are Found

If no relevant skills exist:

1. Acknowledge that no existing skill was found
2. Offer to help with the task directly using your general capabilities
3. Suggest the user could create their own skill with `npx skills init`

Example:

```
I searched for skills related to "xyz" but didn't find any matches.
I can still help you with this task directly! Would you like me to proceed?

If this is something you do often, you could create your own skill:
npx skills init my-xyz-skill
```

## Validation Checklist

### Discovery Mode

- [ ] 识别出用户需求的 domain 和 specific task
- [ ] 已运行 `npx skills find <query>` 至少一次
- [ ] 找到的候选 skill description 与用户需求匹配（命中核心动词）
- [ ] 已向用户展示候选 + install 命令 + skills.sh 链接
- [ ] 用户确认安装意图后才执行 `npx skills add ... -g -y`

### Gap Radar Mode

- [ ] Step R1：已盘点 `~/.agents/skills/`、`~/.claude/skills/`、项目 `.claude/skills/` 三层 inventory
- [ ] Step R2：已识别 ≥ 1 个"反复手动做的事"主题（含频次估计）
- [ ] Step R3：每个主题已做"已覆盖/部分覆盖/未覆盖"三类判定
- [ ] Step R4：未覆盖项已搜过 `npx skills find` + 至少一个备选源
- [ ] Step R5：未命中项已按"频次/稳定性"判定要不要自建
- [ ] Step R6：输出了完整雷达报告（含已盘点 / 候选 gap / 推荐安装 / 推荐自建 / 建议增强）
- [ ] Step R7：推荐自建项已追加到 `~/.agents/skills/skill-analysis/references/evolution-log.md`
