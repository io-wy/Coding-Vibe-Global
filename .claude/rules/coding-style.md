# coding-vibe 编码风格规则

## 通用原则

### 不可变性（Immutability）— 强制

```
❌ WRONG:  modify(original, field, value) → changes original in-place
✅ CORRECT: update(original, field, value) → returns new copy with change
```

- 永远不修改传入的参数
- 永远不就地修改数据结构，返回新副本
- Python 用 `dataclasses.replace()` / Pydantic `.model_copy()`
- Go 用值类型或 `copier` / `deepcopy`
- JS/TS 用 spread operator / `structuredClone` / Immer

### 文件组织

- **多小文件 > 少大文件**
- 200-400 行典型，800 行上限
- 超大模块 → 抽取出工具函数
- 按功能/领域组织目录，不按类型堆叠

```
✅ 按功能: users/ auth/ payments/
❌ 按类型: models/ services/ controllers/
```

### 函数设计

- 单一职责：一个函数只做一件事
- 小函数：≤ 50 行，超过则拆
- 嵌套 ≤ 4 层，否则抽成命名函数
- 参数 ≤ 3 个，超过用 options 对象 / 结构体

### 命名规范

| 元素 | 规范 | 示例 |
|------|------|------|
| 变量 | camelCase | `userName`, `totalCount` |
| 常量/枚举 | UPPER_SNAKE | `MAX_RETRIES`, `Status.OK` |
| 函数/方法 | 动词开头, camelCase | `getUser()`, `validateInput()` |
| 类/类型 | PascalCase | `UserService`, `ApiResponse` |
| 文件/目录 | kebab-case | `user-service.ts`, `auth-handler.go` |
| 数据库 | snake_case | `user_id`, `created_at` |
| URL 路径 | kebab-case | `/api/users/:id` |
| 环境变量 | UPPER_SNAKE | `DB_HOST`, `API_KEY` |

### 错误处理

```python
# ✅ 显式处理
try:
    result = risky_operation()
except NetworkError as e:
    logger.error("Network failure: %s", e)
    return fallback()
except ValidationError as e:
    return {"error": str(e)}, 400

# ❌ 静默吞掉
try:
    result = risky_operation()
except:
    pass
```

- 每个可能失败的调用都要处理错误
- UI 层给用户友好提示，服务端记详细日志
- 不要裸 raise / bare except
- 自定义异常继承自标准异常树

### 输入验证

```python
# ✅ 系统边界验证
from pydantic import BaseModel, EmailStr, Field

class CreateUserInput(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
```

- 所有用户输入在入口验证
- 所有外部数据（API 响应、文件内容）反序列化时验证
- 使用 Schema 验证（Pydantic / zod / 结构体 Tag 验证）
- 失败快（fail fast），给出清晰错误信息

### 注释规范

```python
# 解释 WHY 而非 WHAT（代码本身展示 WHAT）
# ❌ 坏：遍历列表计算总和
# ✅ 好：使用威尔逊区间排序，因为数据量小不需要优化

def wilson_score(votes: int, total: int) -> float:
    """计算威尔逊区间下限，用于置信排序。

    Args:
        votes: 正向票数
        total: 总票数

    Returns:
        威尔逊区间下限值，用于排序

    Raises:
        ValueError: 当 votes > total 时
    """
```

- 公共函数/方法必须有 docstring
- 复杂算法/业务逻辑需要注释 WHY
- TODO 注释必须带 issue 链接或负责人
- 注释不是借口：如果代码需要大量注释才可读 → 重构

## 语言特定规则

### Python
- 类型注解必写（mypy / pyright 严格模式）
- 使用 `ruff` 做 lint + format
- 优先 `httpx` > `requests`
- 配置管理用 `pydantic-settings`
- CLI 用 `typer` / `argparse`
- 测试用 `pytest` + `pytest-cov`

### Go
- 使用 `gofmt` / `golangci-lint`
- 错误处理：永远检查 `err != nil`
- 测试用 `testing` + `testify/assert`

### TypeScript / JavaScript
- 严格模式 TypeScript（`strict: true`）
- 使用 `ESLint` + `Prettier`
- 测试用 `jest` / `vitest`
- 优先 `zod` 做运行时验证

---

*规则是活的。发现更好的风格？PR welcome。*
