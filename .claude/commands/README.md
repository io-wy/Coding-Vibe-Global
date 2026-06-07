# coding-vibe 自定义命令

此目录存放 Claude Code 的自定义 slash 命令。你可以在此注册本 repo 特有的命令。

## 内置命令参考

| 命令 | 用途 | 来源 |
|------|------|------|
| `/loop <interval> <prompt>` | 定期执行任务 | 内置 |
| `/code-review` | 审查当前 diff | 内置 skill |
| `/plan` | 架构方案设计 | 内置 skill |

## 在 coding-vibe 项目中注册命令

将 `.md` 或 `.js` 文件放入此目录，Claude Code 会自动注册为 slash 命令。

### 命令文件示例

```markdown
---
name: convention
description: 检查当前代码是否遵循 coding-vibe 风格
---
请检查当前修改的代码是否遵循 coding-vibe .claude/rules/coding-style.md 中的规则。
列出所有不符合的项。
```

更多信息：https://docs.anthropic.com/en/docs/claude-code/slash-commands
