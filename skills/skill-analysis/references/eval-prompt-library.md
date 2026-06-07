# Eval Prompt Library — Drafting Phase 6 Query Sets

> Templates for composing high-quality `should_trigger` / `should_not_trigger` queries when starting Phase 6 sub-phase 6a.

## 0. 起草哲学

好的 eval set 必须**同时考验召回（FN 防御）和精准（FP 防御）**。两类 query 各自分三档：

```
should_trigger=true:
  ├── 明显（obvious）  — 用 description 的关键词，必须命中，作 sanity check
  ├── 边界（boundary） — 关键词缺失但意图等价，考验语义召回
  └── lifecycle        — 同主题不同生命周期阶段（创建/调试/检查/进化）

should_trigger=false:
  ├── 近义（near-miss） — 相似领域但不该召，考验精准
  ├── 远义（far-miss）  — 完全无关，作 baseline 反例
  └── parasitic        — 看起来像但不该召（借用 description 关键词但意图错位）
```

8-12 个正例 + 8-10 个反例 = 16-22 条总规模。**至少 30% 是边界/近义/parasitic**——只测明显 case 等于不测。

## 1. Reactive Skill 模板

### 示例 skill：brainstorming-with-context

description 摘要：「Use this before any creative work — creating features, building components, adding functionality. Triggered when user says '加功能/修 bug/重构'」

#### should_trigger=true 8 条

| 类别 | Query | 理由 |
|------|-------|------|
| obvious | "加一个登录功能" | 命中 "加功能" |
| obvious | "我想新建一个购物车组件" | 命中 "creating features / building components" |
| boundary | "我想在订单页加个导出 PDF 按钮" | 没说"加功能"但意图等价 |
| boundary | "实现 user 模块的搜索能力" | "实现 ... 能力" 等价 |
| lifecycle | "登录功能不工作了，怎么办" | bug 修复也属创意工作前置 |
| lifecycle | "重构 auth middleware" | 显式命中 "重构" |
| lifecycle | "这个 API 设计是不是该换一下" | redesign 触发 |
| boundary+lifecycle | "Order service 跑不动了，求救" | bug + 自然语言 |

#### should_trigger=false 8 条

| 类别 | Query | 理由 |
|------|-------|------|
| near-miss | "解释下这段代码做什么" | 阅读理解，非创意工作 |
| near-miss | "这个函数怎么用？" | 询问 API，非新建 |
| near-miss | "Go 的 channel 是什么？" | 学习概念，非动手 |
| near-miss | "运行一下测试看看" | 已存在工作的执行 |
| parasitic | "这个 skill 怎么加测试" | 借了"加"字但是元工作 |
| parasitic | "重构 commit message 怎么写好" | 借了"重构"但是文档问题 |
| far-miss | "今天天气怎么样" | 完全无关 |
| far-miss | "帮我订杯咖啡" | 完全无关 |

### 通用 Reactive 模板（替换占位符）

```
should_trigger=true:
  - "{verb_alias_1} {target_object}"           # obvious
  - "{verb_alias_2} a {target_object}"         # obvious (变体)
  - "I want to {goal} the {tangential_object}" # boundary (goal-based)
  - "{lifecycle_verb} the {target_object}"     # lifecycle (debug/refactor/check)
  - "Why isn't {thing} working" + scenario     # lifecycle (debug)
  - "{verb} a new {target_object}"             # obvious
  - "Can you {verb_alias_3} {complex_object}"  # boundary
  - "{natural_phrase}"                         # boundary (用户原声)

should_trigger=false:
  - "What is {target_concept}"                 # near-miss (询问 ≠ 动手)
  - "How does {related_API} work"              # near-miss (学习)
  - "Run {existing_thing}"                     # near-miss (执行 ≠ 新建)
  - "Read me the docs of {object}"             # near-miss (读 ≠ 写)
  - "{verb} the meeting notes"                 # parasitic (同动词不同领域)
  - "{verb_alias} the deploy step"             # parasitic
  - "{unrelated_topic}"                        # far-miss
  - "{personal_question}"                      # far-miss
```

## 2. Enforcement Skill 模板

### 示例 skill：spec-checkpoint

description 摘要：「You MUST use this before phase transitions (requirements → design → implementation → test). Triggered when phase boundary detected」

Enforcement skill 的 Phase 6 less applicable —— 因为 mandate 触发不靠 user query，靠**上下文检测**（"现在要从设计进入实现"）。

但仍可测：

```
should_trigger=true (用户表达 phase 切换意图):
  - "We're done designing, let's start coding"      # 设计 → impl
  - "需求都对齐了，进设计阶段吧"                    # 需求 → 设计
  - "implementation done, run tests"                # impl → test
  - "Time to code this up"                          # 隐含 design done
  - "Let's review the design before writing"        # 设计 → review

should_trigger=false (用户在 phase 内的具体动作):
  - "Add error handling to this function"           # impl 内细节
  - "What's the time complexity here"               # 不切阶段
  - "Run npm test"                                  # 单纯执行
  - "Fix this typo"                                 # 微改
```

提示：Enforcement 测试更关注 **scope clarity** —— 是否只在边界处触发，不过度阻塞日常工作。

## 3. Proactive Skill 模板

### 示例 skill：change-impact-scan

description 摘要：「Automatically triggers when user modifies function signatures / interfaces / data models. Does NOT trigger when only changing internal implementation」

```
should_trigger=true:
  - "Rename function ProcessOrder to HandleOrder"       # 函数名改
  - "Add a new field to User struct"                    # 数据模型
  - "Change the second parameter of authenticate()"     # 签名改
  - "Update the API response to include status"         # 接口改

should_trigger=false:
  - "Optimize the loop inside ProcessOrder"             # 内部实现
  - "Add a debug log to authenticate"                   # 内部
  - "Refactor this if-else into switch"                 # 内部
  - "Fix typo in error message"                         # 微改
```

## 4. 难 case 设计 Tips

### 4.1 Boundary case 必须考验语义召回，不是关键词替换

❌ 弱 boundary：把 "add a feature" 替换成 "add a function"（仅词替换）  
✓ 强 boundary：把 "add a logging feature" 替换成 "我希望服务能记录每次请求"（不同表层，相同意图）

### 4.2 Parasitic case 要触发 false positive trap

设计原则：**借用 description 关键词，但意图不在 skill 范围内**。

例：description 含 "add a feature" → parasitic query: "add a comment to this PR"（借了 add 但意图是评论）

### 4.3 Lifecycle case 测试 stages-beyond-creation 召回

description 大多偏向 "创建"，但 io-wy 实际工作流含 debug/refactor/check/migrate 等阶段。

测试方式：在 query 里**只用** lifecycle 动词（debug/check/audit/migrate），不用 add/create/build。

### 4.4 反例平衡

反例三类参考比例：
- 远义 30% — 基础 baseline，确保不会乱触发
- 近义 40% — 核心精准考验
- parasitic 30% — 陷阱设计

只用远义反例 → 看似 0 false positive 但其实是 trivially negative，没考验任何精准。

## 5. 起草工作流（io-wy 视角）

```
1. Read 目标 skill 的 SKILL.md
2. 提取 description 关键词 + 触发模式
3. 选模板（§1/§2/§3 之一）
4. 替换占位符 → 生成草稿 16-20 条
5. 检查：
   - 正反 1:1 ± 20%? 
   - 30%+ 是边界/parasitic?
   - lifecycle 三个阶段都覆盖?
   - 反例三类齐全?
6. 写 docs-tmp/analysis/<skill>-eval-set-<YYYY-MM-DD>.json
7. 可选：浏览器打开 assets/eval_review.html 让 io-wy 增删改
8. 进入 6b
```

## 6. 验证清单（6a 完成后）

- [ ] 总数 16-22 条
- [ ] 正例 8-12 条，反例 8-10 条，比例不偏斜
- [ ] 正例覆盖三类（obvious/boundary/lifecycle）
- [ ] 反例覆盖三类（near-miss/far-miss/parasitic）
- [ ] 至少 30% 是 boundary 或 parasitic（不只明显 case）
- [ ] query 用户口吻，不是 description 原文
- [ ] query 长度 5-50 字（不太短不太长）
- [ ] should_trigger 标签由起草者主观判断，**不依赖 LLM 自我判断**
