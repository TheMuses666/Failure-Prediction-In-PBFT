import random, simpy, dataclasses
from collections import defaultdict

from simulation.message import Message
from config import (
    BASE_MESSAGE_LATENCY_MS,
    LATENCY_JITTER_MS,
    MESSAGE_DROP_PROBABILITY,
    RANDOM_SEED,
)


class SimPyNetwork:
    """Discrete-event message delivery layer for PBFT simulation."""

    def __init__(
        self,
        env: simpy.Environment,
        latency_mean: float = BASE_MESSAGE_LATENCY_MS,
        latency_std: float = LATENCY_JITTER_MS,
        drop_rate: float = MESSAGE_DROP_PROBABILITY,
        seed: int = RANDOM_SEED,
    ):
        # Save config
        self.env = env
        self.latency_mean = latency_mean
        self.drop_rate = drop_rate
        self.latency_std = latency_std


        # Randomness
        self.rng =random.Random(seed)

        # Initilise defualt
        self.nodes: dict[int, "Node"] = {}
        self.message_log: list[Message] = []
        self.round_stats = defaultdict(lambda:{
            'sent': 0, 'delivered':0, 'dropped':0,
            'delayed': 0, 'replayed':0, 'equivocated':0,
        })
        self.next_message_id = 0

    # =========================
    # Node registration
    # =========================

    def register_node(self, node):
        self.nodes[node.node_id] = node


    # =========================
    # Latency sampling
    # =========================

    def sample_latency(self) -> float:
        raw = self.rng.gauss(self.latency_mean, self.latency_std)
        return max(0.0, raw)


    # =========================
    # Send / Broadcast
    # =========================

    def send_message(self, msg: Message) -> None:
        """
        发送一条消息。普通方法,不 yield,立即返回。
        负责:打 send_time、记日志、累加 sent 计数、启动 _deliver process。
        """
        msg.send_time = self.env.now
        self.message_log.append(msg)
        self.round_stats[msg.round_id]['sent'] +=1
        self.env.process(self._deliver(msg))


    def broadcast(self, sender_id: int, msg_template: Message, receiver_ids: list[int]) -> None:
        """
        把一条消息广播给多个 receiver。普通方法,不 yield。
        提示:每个 receiver 需要一份独立的 Message 副本(避免共享 delivery_time 等字段)。
        """
        for r_id in receiver_ids:
            new_msg = dataclasses.replace(
                msg_template,
                receiver_id = r_id,
                message_id = self._new_message_id()
            )
            self.send_message(new_msg)


    # =========================
    # Internal delivery process
    # =========================

    def _deliver(self, msg: Message):
        """
        SimPy process。这是唯一带 yield 的方法。
        流程:采样延迟 → yield timeout → 判 drop → 写 delivery_time → 投递到 receiver。
        """
        latency = self.sample_latency()
        yield self.env.timeout(latency)

        if self.rng.random() < self.drop_rate:
            self.round_stats[msg.round_id]['dropped'] +=1
            return

        msg.delivery_time = self.env.now
        self.round_stats[msg.round_id]['delivered'] +=1
        self.nodes[msg.receiver_id].receive(msg)

    # =========================
    # Helpers (optional, but handy)
    # =========================

    def _new_message_id(self) -> int:
        """生成自增的消息 id(可选工具方法)。"""
        self.next_message_id += 1
        return self.next_message_id