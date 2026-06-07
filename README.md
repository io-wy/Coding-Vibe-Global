# 🎯 coding-vibe-global

**企业级个人 Claude Code 方法论体系核心仓库。**

让每个项目在被 Claude Code 打开时，自动获得你专属的编码规范、工作流约定和 AI 协作策略。

## 使用场景

### 🆕 我是新用户，刚下载 Claude Code

参见 [docs/bootstrap.md](docs/bootstrap.md) → 配 MCP、装 Skill、找 Key。

### 📦 新 Go 项目

```bash
git clone https://github.com/io-wy/Coding-Vibe-Go.git ~/my-project
cd ~/my-project
claude
```

### 📦 现有项目接入

```bash
cp .claude/rules/*.md /path/to/your-project/.claude/rules/
cp .claude/settings.json /path/to/your-project/.claude/
```

### 🔄 规则同步

在 coding-vibe-global 编辑规则并提交，各项目 `git pull` 拉取模板更新即可。

## 体系概览

```
coding-vibe-global/          ← 中央知识库（本仓库）
├── CLAUDE.md                Claude Code 读取后获知方法论
├── .claude/rules/           共享规则（编码、Git、审查、方法论）
├── setup.sh                 初始化 / 同步 CLI 工具
└── templates/               项目模板

coding-vibe-<lang>/          ← 项目级仓库（如 coding-vibe-go）
├── CLAUDE.md                ← 项目标识，引用全局规则
└── .claude/rules/           ← 从全局同步来的规则副本
```

## 规则文件

| 规则 | 说明 |
|------|------|
| `methodology.md` | AI 协作三层模型、信息分级策略、工作流循环 |
| `coding-style.md` | 不可变性强制、命名规范、文件组织、语言特定规则 |
| `git-workflow.md` | 分支策略、Conventional Commits、Code Review 流程 |
| `review-checklist.md` | 功能/安全/性能/可维护性/测试检查清单 |

## 快速链接

- [🚀 新机引导](docs/bootstrap.md) — 新装 Claude Code 从这里开始
- [方法论全文](.claude/rules/methodology.md)
- [编码风格](.claude/rules/coding-style.md)
- [Git 工作流](.claude/rules/git-workflow.md)
- [审查清单](.claude/rules/review-checklist.md)
- [项目模板](templates/)
- [setup.sh](setup.sh)

## 原理

当 Claude Code 在项目目录中启动时：
1. 读取根目录 `CLAUDE.md` → 获得项目上下文
2. 加载 `.claude/rules/*.md` → 获得方法论规则
3. 读取 `.claude/settings.json` → 获得运行时配置

编码-vibe 体系劫持这三个入口，让每个项目自动继承你的个人开发哲学。

---

**维护者**：io-wy | **版本**：1.0 | **更新**：2025-06
