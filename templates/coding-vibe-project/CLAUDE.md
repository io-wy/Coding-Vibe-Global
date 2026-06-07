# 项目名

## 技术栈

- **语言/框架**：[如 Go 1.22 / Gin]
- **数据库**：[如 PostgreSQL 16]
- **基础设施**：[如 Docker / K8s]
- **CI/CD**：[如 GitHub Actions]
- **测试**：[如 pytest / testify]

## 项目结构

```
.
├── cmd/           # 入口
├── internal/      # 内部实现
├── pkg/           # 可导出的包
├── api/           # API 定义（OpenAPI、proto）
├── migrations/    # 数据库迁移
├── scripts/       # 工具脚本
├── deploy/        # 部署配置
└── docs/          # 文档
```

## 编码约定

此项目遵循 **coding-vibe 方法论** 的所有规则：

### 引用方式

coding-vibe 全局方法论在 `C:\code\starter\coding-vibe\coding-vibe-global`。

关键规则文件已复制到 `.claude/rules/` 目录，Claude Code 会自动加载。

### 项目特定规则

- [项目特有的约定，如：使用 Uber Zap 做日志]
- [其他特殊要求]

## 快速开始

```bash
# 开发环境启动
make dev

# 运行测试
make test

# lint
make lint
```

## 环境变量

参见 `.env.example`

---

*请保持 CLAUDE.md 随项目演进同步更新。*
