"""自拟反例：分组跨tick续传时，未发完的记录不得计为交付，且余量只能给队首。
揭示的错误：把部分发送误报为完成，或没发完A就提前发送B。
"""
from src.models import Arrival, Config
from src.utils import simulate
from src.metrics import summarize


def test_partial_then_fifo():
    cfg = Config(users=1, ticks=3, slot_bits=128, tick_ms=1, header_bits=32)
    # 手算：A=300bit→wire 332，B=32bit→wire 64，两者同tick到达且缓存足够
    # tick0: A发128，余204
    # tick1: A发128，余76
    # tick2: A发76完成（delay=3ms，弹出），余预算52给B，B余12
    # 结果：交付300，积压32，丢弃0，线速发送384 = 3×128
    raw = simulate([Arrival(0, 0, 300), Arrival(0, 0, 32)], cfg, 'packet')
    m = summarize(raw, cfg)
    assert raw['delivered_payload_bits'] == 300
    assert raw['backlog_payload_bits'] == 32
    assert raw['dropped_payload_bits'] == 0
    assert raw['wire_sent_bits'] == 384
    assert [v['wire_bits'] for v in raw['trace']] == [128, 128, 128]
    assert m['payload_utilization'] == 300 / 384
    assert m['mean_delay_ms'] == 3.0
    assert m['max_delay_ms'] == 3.0
