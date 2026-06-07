# 🚀 新机引导

```bash
# 1. 克隆
git clone <repo-url> ~/coding-vibe/coding-vibe-global
cd ~/coding-vibe/coding-vibe-global

# 2. MCP（填 key 后生效）
cp mcp.example.json ~/.claude/mcp.json

# 3. Skill（全部复制）
cp -r skills/* ~/.claude/skills/

# 4. 完工
claude
```

## 取 Key

| MCP | 免费额度 | 链接 |
|-----|----------|------|
| Brave Search | 2000次/月 | https://api.search.brave.com/app/ |
| Exa | 1000次/月 | https://exa.ai/ |
| Tavily | 1000次/月 | https://tavily.com/ |

填到 `~/.claude/mcp.json` 对应的 `""` 里。

## 然后

- **新 Go 项目**：`git clone https://github.com/io-wy/Coding-Vibe-Go.git`
- **现有项目**：把 [.claude/rules](../.claude/rules) 复制过去
