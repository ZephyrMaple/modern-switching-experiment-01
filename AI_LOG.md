# AI协作记录

工具与模型：WorkBuddy（DeepSeek-V4.1-Flash），用于代码解释、实现建议与报告结构整理；所有结论均以本机测试和手算为准。

## 一项真实协作过程

需求与输入：补全 `src/part1_circuit.py` 的 `serve_circuit`。提供的信息包括函数 docstring（`queues` 为每用户一个 `deque[Pending]`，原地更新；仅服务 `tick % cfg.users`；返回 `(wire_bits, completed)`）、`Config` 默认参数（4 用户、128 bit/tick）和验收用例 AC01/AC02 的文字描述。

AI建议：先算 `user = tick % cfg.users` 取该用户队列；用 `while q and sent < cfg.slot_bits` 循环，每次 `give = min(head.remaining_wire_bits, cfg.slot_bits - sent)`，扣减 `remaining_wire_bits` 并累加 `sent`；仅当 `remaining_wire_bits == 0` 时 `popleft()` 并加入完成列表。并提示三个易错点：空时隙不得借给他人、部分发送不得 popleft、预算有剩要接着发下一条。

我的手算与测试：先按 PRD 6.1 手算 2 用户 2 tick 的 96 bit 例子，预期电路 tick 0 发 0、tick 1 发 96 于 2 ms 完成，有效利用率 37.5%、线路忙碌率 37.5%。实现后运行 `grading/test_circuit.py`，4 passed（`test_idle`、`test_reserved_user_only`、`test_partial`、`test_fifo_budget`）。为验证边界，另写 `student_tests/test_my_case.py`：A=300 bit、B=32 bit 同 tick 到达，手算 tick 余量 332→204→76→0，预期交付 300、积压 32、线速 384、时延 3.0 ms，运行 1 passed。

修正或采纳理由：AI 的首版建议没有提到 `Pending` 是可变 dataclass，我核对 `src/models.py` 后确认可以原地扣减，但 `payload_bits` 必须保持原值（积压统计依赖它），因此仅修改 `remaining_wire_bits`。另外 AI 首版把"预算用完"写成 `break` 之外还加了"队列空则结束"，实际 `while q` 已覆盖，删除冗余判断。首次建议基本正确，但仍以手算的两个数值（37.5%/2 ms 与 300/32/384）和 5 项测试作为采纳依据，而非"测试全绿"本身。

我能解释的核心逻辑：`give` 取 `min(剩余 wire, 剩余预算)` 保证不超过 128 bit；`remaining_wire_bits == 0` 是"完成"的唯一判据，因此部分发送的记录留在队首，下一 tick 继续从断点续传，不会重复计费也不会被误记为交付；分组函数里 `remaining_wire_bits` 已由框架初始化为 `payload_bits + header_bits`，所以实现中不再加 32 bit，否则 AC03 的 128 会变成 160 而超出预算。
