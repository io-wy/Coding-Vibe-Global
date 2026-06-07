# Phase 6: Empirical Verification — Detailed Procedure

> Where 论证主义 ends and 实证主义 begins. Phase 6 measures actual trigger behavior of a skill description, replacing文本审 with executable evidence.

## 0. 设计哲学

### 三句话回顾
1. **该用时召不出，比不召更糟** — 测 should_trigger 真实命中率
2. **不该用时硬召，比召不出更糟** — 测 should-not-trigger 反例
3. **改完没测就不算改** — train/test split + 自动重测 + 按 test 选最优

### 与 Phase 1 的关系
- Phase 1.3 的 quantitative penalties (phrase count, verb diversity, domain anchor, NL alignment) 是**经验启发** — 凭文本特征推测召回质量
- Phase 6 是**实证测量** — 让 Claude 真的看到这个 description，跑 N 次，测真实命中率
- 当二者结论冲突：**实证为准**，但报告必须列两个分数 + 冲突原因

## 1. 何时启用 / 何时跳过

### 启用条件（任一满足）
1. io-wy 显式说"实证验证 / run skill eval / measure recall / empirical verification"
2. Phase 1 给分 65-75（borderline，论证不可信）
3. Phase 5.4 提议改 description，需要实证证据再合并
4. 二选一描述（io-wy 想在 A/B 间挑）

### 跳过条件（满足任一就跳）
1. Quick scan / 只读分析（不值这个成本）
2. Skill 是 Enforcement / Proactive 模式（Phase 6 主测召回，对这两类不适用）
3. 没有 ANTHROPIC_API_KEY 环境变量
4. 估算成本 > $5 且 io-wy 没显式批

## 2. 子阶段 6a：Draft Eval Set

### 目标
为目标 skill 起草 16-20 条带 should_trigger 标签的 eval queries。

### 输入
- 目标 skill 的 SKILL.md 路径
- 目标 skill 的 description 当前文本
- skill 的触发模式（Phase 0 输出）

### 行动
1. Read SKILL.md，提取 description + skill 名 + 触发模式
2. 加载 `references/eval-prompt-library.md` 对应模式的模板
3. 生成 16-20 条 query：
   - 8-12 条 `should_trigger=true`（覆盖三类：明显/边界/lifecycle）
   - 8-10 条 `should_trigger=false`（覆盖三类：近义/远义/parasitic）
4. 写入 `docs-tmp/analysis/<skill-name>-eval-set-<YYYY-MM-DD>.json`
5. 可选：调起 `assets/eval_review.html` 让 io-wy 浏览器审 query

### 输出格式

```json
[
  {"query": "Add a logging skill", "should_trigger": true, "category": "obvious"},
  {"query": "How do I write a Python class?", "should_trigger": false, "category": "far-miss"}
]
```

`category` 字段可选，便于日后追责到哪类 query 出错。

### 常见错误
| 错误 | 后果 | 预防 |
|------|------|------|
| 全是明显正例 | 测出来都 pass，没区分度 | 强制 25%+ 是边界 case |
| 反例只用远义 | 不测 false positive 风险 | 反例必须含 30%+ 近义 |
| 抄 trigger phrases 当 query | 等于自己测自己 | query 必须用户口吻，不引用 description 原文 |
| query 太短 | <5 字的不真实 | query 模拟真实用户问题，10-30 字为佳 |

## 3. 子阶段 6b：Stratified Train/Test Split

### 算法

```python
def split_eval_set(eval_set, holdout=0.4, seed=42):
    pos = [e for e in eval_set if e["should_trigger"]]
    neg = [e for e in eval_set if not e["should_trigger"]]
    random.seed(seed)
    random.shuffle(pos)
    random.shuffle(neg)
    n_pos_test = max(1, int(len(pos) * holdout))
    n_neg_test = max(1, int(len(neg) * holdout))
    test = pos[:n_pos_test] + neg[:n_neg_test]
    train = pos[n_pos_test:] + neg[n_neg_test:]
    return train, test
```

### 关键参数
- `holdout=0.4` — 默认 40% 进 test
- `seed=42` — 固定，保证多次运行可复现 + 可比对
- **分层切分** — 正反例各自独立切，保证 test 集两类都有

### 输出
内存中的 `(train_set, test_set)` tuple，不落盘。

## 4. 子阶段 6c：Baseline Eval

### 目标
用当前 description 跑一次完整 eval，得到 baseline 触发率。

### 算法
对 train + test 合并集合（不在 6c 阶段拆开测，节省 SDK 调用）：
- 每条 query 跑 `runs_per_query=3` 次
- 每次跑：用 Anthropic SDK 启动 messages.stream，注入伪 skill 到 system prompt
- 触发判定：流式扫 content_block_start / content_block_delta，看是否输出 `<skill_call name="{skill_name}"`
- 多数投票：`trigger_rate ≥ threshold (0.5)` 且 `should_trigger=true` → pass

### 输出（baseline_results.json）

```json
{
  "skill_name": "...",
  "description": "...",
  "results": [
    {"query": "...", "should_trigger": true, "trigger_rate": 0.67,
     "triggers": 2, "runs": 3, "pass": true}
  ],
  "summary": {"total": 16, "passed": 13, "failed": 3}
}
```

### Windows / Threading 实现要点

**不用 select.select**（Windows pipe 不支持），改用 threading.Thread + queue.Queue 读 stream：

```python
import threading
import queue

def stream_reader(stream, q):
    try:
        for event in stream:
            q.put(("event", event))
        q.put(("done", None))
    except Exception as e:
        q.put(("error", e))

q = queue.Queue()
t = threading.Thread(target=stream_reader, args=(stream, q), daemon=True)
t.start()

deadline = time.time() + timeout
triggered = False
while time.time() < deadline:
    try:
        kind, payload = q.get(timeout=1.0)
    except queue.Empty:
        continue
    if kind == "done":
        break
    if kind == "error":
        raise payload
    # process event payload
    if check_trigger(payload, skill_name):
        triggered = True
        break  # early stop

# cleanup: thread is daemon, will exit with main
```

详细实现见 `scripts/run_eval.py`（Batch 2 移植）。

## 5. 子阶段 6d：Iterate (Optional)

### 触发条件
- Phase 5.4 提议改 description
- io-wy 说"自动改"

### 主循环

```python
for iter in range(1, max_iterations + 1):
    results = run_eval(train + test)
    train_results, test_results = split_back(results, train, test)
    history.append({
        "iter": iter, "description": current_desc,
        "train_passed": ..., "train_failed": ...,
        "test_passed": ..., "test_failed": ...,
        "results": results,
    })
    if train_failed == 0:
        break  # all train pass
    if iter == max_iterations:
        break

    # blinded history: strip test_* fields before passing to LLM
    blinded = strip_test_fields(history)
    new_desc = improve_description(skill, current_desc, train_results, blinded)
    current_desc = new_desc

# 选最优
if test_set:
    best = max(history, key=lambda h: h["test_passed"] or 0)
else:
    best = max(history, key=lambda h: h["train_passed"])
```

### 防过拟合三件套
1. **Stratified split** (6b) — 正反比例均衡
2. **Blinded history** — improve_description 看不到 test 性能
3. **按 test 选 best** — 不按 train，避免 train 100% 但 test 崩

### 默认参数
- `max_iterations=5`（cap 10）
- `runs_per_query=3`
- `trigger_threshold=0.5`
- `holdout=0.4`

## 6. 子阶段 6e：Report & 回灌

### HTML 报告
- 由 `scripts/generate_report.py` 渲染
- 行=iteration，列=每条 query 的 ✓/✗
- best 行 highlight
- auto-refresh 5s
- 落 `docs-tmp/analysis/<skill>-eval-<date>.html`

### Markdown summary
落 `docs-tmp/analysis/<skill>-eval-summary-<date>.md`，含：
- baseline vs best 对比
- per-query 表（test set）
- iteration history 表
- 与 Phase 1 论证的冲突

### 回灌路径

| 目标 | 怎么灌 |
|------|--------|
| Phase 1 报告 | Phase 1.6 输出末尾追加 "Empirical override: <yes/no> — <reason>" |
| Phase 5.4 change set | best_description 替代 LLM first-draft 作为最终描述 |
| references/evolution-log.md | 该 cycle record 末尾追加 Phase 6 summary 表 |

## 7. SDK Setup（Anthropic SDK 路径）

### 环境变量
```bash
export ANTHROPIC_API_KEY=sk-ant-xxx
```

### Python 依赖
```bash
pip install anthropic
```

### 关键 API：messages.stream()
```python
import anthropic

client = anthropic.Anthropic()  # 自动读 ANTHROPIC_API_KEY
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=system_prompt_with_skill,
    messages=[{"role": "user", "content": query}],
) as stream:
    for event in stream:
        # process content_block_start / content_block_delta / message_stop
```

### 模拟 available_skills 的 system prompt

skill-creator 走 `claude -p` CLI，借用 Claude Code 的 available_skills 注入；我们走 SDK，必须自己在 system prompt 里**模拟**这个机制：

```
You have access to the following skills:

- {skill_name}: {description}

When a user request matches a skill's description, invoke it by outputting:
<skill_call name="{skill_name}" />

If no skill matches, respond normally.
```

trigger 判定改成扫 `<skill_call name="{skill_name}"` 标签。

> ⚠️ **不确定性声明**：此 system prompt 模板未实测。Batch 2 实施时**必须先做 sanity check**：用一个已知会触发的 query + 一个已知不会触发的 query 跑 5 次,看 trigger_rate 是否分别接近 1.0 和 0.0。如果不收敛,需要调 system prompt 措辞或加 few-shot。

> ✅ **2026-05-03 sanity check 通过**(详见 `docs-tmp/analysis/phase6-sanity-check-2026-05-03.md`):
> - Endpoint: Kimi proxy (`ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`)
> - 阳性 query 5/5 触发,阴性 query 1/5 触发
> - 机制有效,但 Kimi 在 far-miss query 上有约 20% baseline 假阳性率。`runs_per_query=3` + `threshold=0.5` 仍能正确分类大多数 case。boundary 附近的 query 建议跑 5 次或将阈值提到 0.67。
> - 切换 endpoint(例如换真 Anthropic 或 Bedrock)需重跑 sanity check 校准。

## 8. 成本估算公式

```
queries × runs_per_query × iterations × cost_per_call
= 16 × 3 × 5 × $0.012
≈ $2.88 per Phase 6 full cycle
```

实际 cost 取决于：
- 模型选择（Sonnet 4.6 ≈ $3 / 1M input + $15 / 1M output）
- 平均 token 数（system prompt + query ≈ 1.5k input；输出 ≈ 0.3k）
- iteration 实际跑了多少（早 break 节省）

### 守门员逻辑

```python
estimated_cost = queries * runs * iterations * cost_per_call
if estimated_cost > 5.0:
    print(f"⚠️ Estimated cost ${estimated_cost:.2f} exceeds $5 threshold.")
    print("Confirm with [io-wy approve] before proceeding.")
    if not user_confirmed:
        sys.exit(1)
```

## 9. 常见错误

| 错误 | 后果 | 预防 |
|------|------|------|
| 没设 ANTHROPIC_API_KEY | SDK 401 | 启动前 check 环境变量 |
| 用 select.select 在 Windows | 卡住或异常 | 用 threading.Thread + queue 替代 |
| 直接信任 LLM 改写后的 description 不再测 | 过拟合 train | 按 test_passed 选 best |
| Eval set 全是正例 | 没法测 false positive | 强制 30%+ 反例 |
| 没固定 seed | 多次结果差异大 | seed=42 写死 |
| baseline 100% pass 仍触发 iterate | 浪费时间和钱 | iterate 前 if train_failed==0: skip |
| HTML 报告写错路径 | io-wy 看不到结果 | 用 `docs-tmp/analysis/` 不要自创目录 |

## 10. 输出 schema 总览

### eval_set.json（6a 输出）
```json
[{"query": "str", "should_trigger": true, "category": "obvious|boundary|lifecycle|near-miss|far-miss|parasitic"}]
```

### baseline_results.json / iteration_results.json（6c/6d 输出）
```json
{
  "skill_name": "str",
  "description": "str",
  "iteration": 0,
  "results": [
    {"query": "str", "should_trigger": true, "trigger_rate": 0.0,
     "triggers": 0, "runs": 3, "pass": false}
  ],
  "summary": {"total": 0, "passed": 0, "failed": 0}
}
```

### history.json（6d 输出）
```json
{
  "skill_name": "str",
  "started_at": "ISO-8601",
  "max_iterations": 5,
  "best_iteration": 2,
  "best_description": "str",
  "iterations": [{
    "iter": 1,
    "description": "str",
    "train_passed": 0, "train_failed": 0,
    "test_passed": 0, "test_failed": 0,
    "results": []
  }]
}
```

## 11. 验证清单

- [ ] eval_set 有 16+ 条 query，正反比例 1:1 ± 20%
- [ ] eval_set 含至少 30% 边界 case（不只明显正反）
- [ ] split 用了 stratified + seed=42
- [ ] runs_per_query ≥ 3
- [ ] 启动前打了成本估算
- [ ] 改写时用 blinded history
- [ ] 选 best 用 test_passed
- [ ] 报告同时记录论证 + 实证两个分数
- [ ] 结果写入 `docs-tmp/analysis/`，路径符合 CLAUDE.md 约定
