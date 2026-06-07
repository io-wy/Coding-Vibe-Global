# coding-vibe 规则目录

本目录包含 coding-vibe 方法论的可复用规则文件。Claude Code 会自动加载这些文件作为系统指令的一部分。

## 文件列表

| 文件 | 用途 | 引用方式 |
|------|------|----------|
| `methodology.md` | 核心 AI 协作方法论 | 每个项目都应有 |
| `coding-style.md` | 编码风格与命名约定 | 按语言选择适用部分 |
| `git-workflow.md` | 分支策略与 commit 规范 | git 项目必备 |
| `review-checklist.md` | 代码审查检查清单 | 审查时参考 |

## 引用规则

在项目 CLAUDE.md 中通过以下方式引用：

```markdown
<!-- 引用全局规则（在 coding-vibe-global 仓库中） -->
此项目遵循 coding-vibe 方法论，详见：
- /path/to/coding-vibe-global/.claude/rules/methodology.md
- /path/to/coding-vibe-global/.claude/rules/coding-style.md
```

或在使用 setup.sh 初始化后，规则文件会直接复制到项目 `.claude/rules/` 目录，
Claude Code 会自动加载。

## 添加新规则

1. 在 `/.claude/rules/` 创建新的 `.md` 文件
2. 更新本 README 的索引表
3. 更新 `CLAUDE.md` 的规则索引
4. 提交 PR

### 规则文件模板

```markdown
# rule-name — 简短描述

## 适用范围

<什么情况下这条规则被触发使用>

## 规则内容

<具体的规则条目>

## 例外

<什么情况下可以打破这条规则>
```
