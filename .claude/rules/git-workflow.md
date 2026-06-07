# coding-vibe Git 工作流

## 分支策略

```
main          ← 生产就绪（只合并，不直接提交）
  ├── feat/xxx     ← 新功能
  ├── fix/xxx      ← 修复
  ├── refactor/xxx ← 重构
  └── chore/xxx    ← 杂项（CI、文档、配置）
```

### 规范
- **main**：受保护分支，仅通过 PR 合并
- **功能分支**：从 main 创建，合并后删除
- **命名**：`<type>/<简短描述>`，如 `feat/user-auth`, `fix/null-pointer`
- **类型**：`feat` `fix` `refactor` `chore` `docs` `test` `perf` `style`

## Commit 规范

使用 **Conventional Commits**：

```
<type>(<scope>): <简短描述>

<可选：详细正文>

<可选：footer（如 BREAKING CHANGE, Closes #123）>
```

### 类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(auth): add OAuth2 login flow` |
| `fix` | 修复 | `fix(parser): handle null input gracefully` |
| `refactor` | 重构 | `refactor(api): extract validation middleware` |
| `chore` | 杂项 | `chore(deps): update pydantic to v2` |
| `docs` | 文档 | `docs(readme): add setup instructions` |
| `test` | 测试 | `test(user): add edge cases for email validation` |
| `perf` | 性能 | `perf(cache): reduce TTL for hot keys` |
| `style` | 格式 | `style(rust): cargo fmt` |

### 规则
- **原子提交**：一个 commit 只做一件事
- **描述用祈使句**（"Add", "Fix", "Remove"，不是 "Added", "Fixes"）
- **正文**：解释 WHY 而非 WHAT
- **关联 issue**：`Closes #123` / `Refs #456`
- CI 失败 → 禁止合并到 main

## Code Review 流程

### 提交 PR 前
- [ ] 自测通过（单元测试 + 集成测试）
- [ ] lint / type-check 无报错
- [ ] 无调试代码、注释代码、TODO（有 TODO 需有 issue）
- [ ] commit 信息符合规范

### Review 时重点检查
1. **正确性**：逻辑是否正确？边界条件覆盖？
2. **安全性**：输入验证？SQL 注入？XSS？
3. **性能**：N+1 查询？不必要的重复计算？
4. **可维护性**：命名清晰？函数单一职责？测试可读？

### 合并策略
- 默认 **Squash merge**（保持 main 历史干净）
- 多个人协作同一功能 → **Merge commit**（保留分支历史）
- 禁止 **Rebase merge** 到 main（除非确认所有人都 rebase 过）

## 标签与发布

```
v1.0.0 → v1.1.0 → v1.2.0 → v2.0.0
 ^major   ^minor   ^patch   ^breaking
```

- **major**：不兼容 API 变更
- **minor**：向后兼容的新功能
- **patch**：向后兼容的修复
- 使用 `git tag -s`（签名的 annotated tag）
- 发布时生成 Changelog

## 配置参考

### .gitignore 必备项

```
# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build
dist/
build/
*.exe
*.dll
*.so

# Environment
.env
.env.local
*.local.json
__pycache__/
*.pyc
node_modules/
.venv/
```

---

*Git 历史的干净 = 项目健康的信号。维护好它。*
