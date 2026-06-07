# coding-vibe global — 企业级 Claude Code 方法论中心

本仓库是 **coding-vibe 方法论体系**的中央知识库与分发中心。当你在此仓库中打开 Claude Code 时，你将获得完整的 coding-vibe 工作流认知。

## coding-vibe 是什么

一套可复用的、版本化控制的 **Claude Code 工作流配置体系**，让每个项目在被 Claude Code 打开时自动获得：

- 方法论上下文（如何与 AI 协作开发）
- 编码规范与风格约束
- Git 工作流约定
- 代码审查标准
- 项目级自定义命令（slash commands）

## 体系架构

```
coding-vibe-global/              ← 你在的地方——全局方法论（本仓库）
├── CLAUDE.md                     ← 本文件，Claude 加载时的入口
├── mcp.example.json             ← MCP 服务器配置（复制到 ~/.claude/）
├── skills/                       ← Skill 文件（复制到 ~/.claude/skills/）
├── .claude/rules/*.md            ← 共享规则，可被其他项目引用
└── docs/bootstrap.md             ← 新机引导

其他项目：参见 [Coding-Vibe-Go](https://github.com/io-wy/Coding-Vibe-Go.git)
```

## 规则索引

| 文件 | 用途 |
|------|------|
| `.claude/rules/coding-style.md` | 编码风格与命名约定 |
| `.claude/rules/git-workflow.md` | 分支策略与 commit 规范 |
| `.claude/rules/review-checklist.md` | 代码审查检查清单 |
| `.claude/rules/methodology.md` | 核心 AI 协作方法论 |

## 快速使用

### 新机引导

详见 [docs/bootstrap.md](docs/bootstrap.md) — MCP 配置 + Skill 安装 + 找 Key。

### 新项目

```bash
# 复制 Go 模板到新目录
cp -r templates/coding-vibe-go /path/to/new-project
cd /path/to/new-project
# 改 go module 名
sed -i '' 's|io-wy/go-backend-starter|你的-module名|' go.mod
```

### 现有项目

```bash
# 复制规则到现有项目
cp .claude/rules/*.md /path/to/your-project/.claude/rules/
cp .claude/settings.json /path/to/your-project/.claude/
```

## 协作流程

1. **方法论演进**：规则在本仓库经审查后合并 → 各项目 `git pull` 同步
2. **项目专属覆盖**：项目级 `.claude/rules/` 可覆盖全局规则（同名文件优先）
3. **版本追踪**：所有规则在 git 中，可 diff、review、rollback

## 约定

- 本仓库本身不包含业务代码，只包含方法论和配置
- 规则文件使用 Markdown，行数 ≤ 400 行
- 每个规则文件都有明确的触发条件和适用范围
- 所有路径引用使用 POSIX 风格（`/c/...`）

---

*当你在此仓库中时，你是 coding-vibe 方法论的管理员。维护好这套配置，让每个项目都有一个熟悉的开发副驾。*
