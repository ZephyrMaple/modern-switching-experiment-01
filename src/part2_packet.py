"""任务2：补全共享FIFO分组交换发送。"""
def serve_packet(queue, tick, cfg):
    """queue为共享deque[Pending]，原地更新。
    remaining_wire_bits已由框架初始化为payload_bits+header_bits，不再重复加包头。
    每tick发送不超过slot_bits；必须发完队首再处理下一项。
    分组允许跨tick续传，但不得与其他分组交错，不能因大于一个时隙就丢弃。
    返回(线速发送比特数,完整发送的Pending列表)；空队列返回(0,[])。
    """
    sent = 0
    done = []
    while queue and sent < cfg.slot_bits:
        head = queue[0]
        give = min(head.remaining_wire_bits, cfg.slot_bits - sent)
        head.remaining_wire_bits -= give
        sent += give
        if head.remaining_wire_bits == 0:
            done.append(queue.popleft())
    return sent, done
