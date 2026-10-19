# AI协作记录

工具与模型：WorkBuddy（DeepSeek-V4.1-Flash）。用于阅读 PRD、解释模型规则、给出实现建议、整理报告框架；所有数值结论以本地 pytest 与手算为准。

## 一项真实协作过程

需求与输入：补全 `src/part1_circuit.py` 的 `serve_circuit`。提供给 AI 的约束包括：`queues` 是每用户一个 `deque[Pending]`；只服务 `tick % cfg.users`；单 tick 预算 `cfg.slot_bits = 128`；返回 `(wire_bits, completed)`；AC01（当前用户为空时不得借用他人时隙）、AC02（200 bit 记录在 128 bit 容量下分两 tick 完成）。另要求先解释规则再给实现，一次只补一个函数。

AI建议：先取 `user = tick % cfg.users` 与该用户队列；用 `while q and sent < cfg.slot_bits` 循环，每轮 `give = min(head.remaining_wire_bits, cfg.slot_bits - sent)`，扣减后累加 `sent`；仅当 `remaining_wire_bits == 0` 时 `popleft()` 并加入完成列表；预算归零即结束本轮。同时列出三处易错：空时隙借给他人、部分发送被误记完成、发完一条就停下而不用剩余预算。

我的手算与测试：先按 PRD 6.1 手算 2 用户 2 tick 的 96 bit 例子，预期电路 tick 0 发 0、tick 1 发 96 于 2 ms 完成，有效利用率 37.5%、线路忙碌率 37.5%，并与分组（1 ms、50%）对照。实现后运行 `grading/test_circuit.py`，4 passed（`test_idle`、`test_reserved_user_only`、`test_partial`、`test_fifo_budget`）。同一循环结构用于 `serve_packet`，`test_packet.py` 4 passed；`summarize` 按守恒式实现，`test_metrics.py` 3 passed，集成 3 passed，全量 23 passed。

修正或采纳理由：AI 的实现直接原地改写 `remaining_wire_bits`。我核对 `src/models.py` 后确认 `Pending` 是可变 dataclass、可原地扣减，但 `payload_bits` 必须保持原值（积压统计依据它），因此限定只改 `remaining_wire_bits`。分组函数中 AI 提示框架已把 `remaining_wire_bits` 初始化为 `payload_bits + header_bits`，不应再加 32 bit；我按 AC03 核对：96+32 = 128 恰好一个时隙，若重复加头会变成 160 而超出预算，据此采纳。首次建议即基本正确，但仍以两个手算结果（37.5%/2 ms 与反例的 300/32/384）和 5 项测试作为采用依据。

我能解释的核心逻辑：`give = min(剩余 wire, 剩余预算)` 保证单 tick 不超过 128 bit；`remaining_wire_bits == 0` 是完成的唯一判据，因此部分发送的记录留在队首、下一 tick 从断点续传，既不会重复计费也不会被误记为交付；预算有剩余时必须继续处理下一条，否则 AC05 中两条 48 bit 记录只会完成一条。

## 其余协作与我的验证

| 事项 | AI 产出 | 我的核对 |
|---|---|---|
| 自拟反例 | 建议 A=300 bit、B=32 bit 同 tick 到达，跨 3 tick 完成 | 手算余量 332→204→76→0，预期交付 300、积压 32、线速 384、时延 3.0 ms；`test_my_case.py` 1 passed |
| 参数扫描 | 首版输出 5 个包头值 × 4 场景 × 2 模型共 40 行 | 电路行重复 5 次属冗余，改为 24 行（电路仅留基线一行），条件与结论写入报告 |
| 报告初稿 | 生成 9 节框架并填入 8 行实测数据 | 补 `synchronized_burst` 不能作为优劣证据、补可复现条目；重跑 `performance_test.py` 后 `comparison.csv` 的 MD5 一致 |
| 仓库检查 | 列出与基线的差异，指出 `.venv`、`__pycache__`、评分产物不应提交 | 按 PRD 11.12 用 `git add -f` 单独添加 7 个结果文件 |

模型规则与验收标准来自 PRD 与教师测试，AI 只负责实现建议与结构整理；最终 commit、推送与是否创建 PR 由本人决定。
