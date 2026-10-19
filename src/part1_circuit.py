"""任务1：补全固定时隙电路交换发送。只改本文件内TODO。"""
def serve_circuit(queues, tick, cfg):
    """queues为每用户一个deque[Pending]，原地更新。
    本tick只能服务user=tick % cfg.users，其他用户不能借用其时隙。
    该用户可在slot_bits预算内连续发送多个记录，也可部分发送一个记录。
    返回(本tick实际线速发送比特数, 本tick完整发送的Pending列表)。
    空队列返回(0,[])；记录完全发完才pop并记入完成列表。
    提示：先确定用户，再在该用户队列上按FIFO扣减remaining_wire_bits。
    """
    q = queues[tick % cfg.users]
    sent = 0
    done = []
    while q and sent < cfg.slot_bits:
        head = q[0]
        give = min(head.remaining_wire_bits, cfg.slot_bits - sent)
        head.remaining_wire_bits -= give
        sent += give
        if head.remaining_wire_bits == 0:
            done.append(q.popleft())
    return sent, done
