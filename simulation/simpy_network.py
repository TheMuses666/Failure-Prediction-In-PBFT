"""
SimPy-based discrete-event message delivery layer.

The network owns the SimPy Environment for the simulation. Every message
is delivered via a SimPy process that yields a timeout to advance simulated
time; no wall-clock sleeping is used. This lets a full PBFT round run in
a fraction of a real second.

Design contract:
  - send_message / broadcast are plain methods that register events and
    return immediately (no yield).
  - _deliver is the only generator (process): it yields env.timeout(latency),
    then evaluates the drop decision *after* the timeout so the drop event
    is logged at the moment the message physically would have arrived.
  - All randomness goes through self.rng so a fixed seed makes a run
    fully reproducible (required for paper-grade experiments).
"""

import random
import dataclasses
from collections import defaultdict

import simpy

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
        fault_injector=None
    ):
        # SimPy scheduler and latency / drop configuration.
        self.env = env
        self.latency_mean = latency_mean
        self.latency_std = latency_std
        self.drop_rate = drop_rate
        # Phase 4 attacker hook. None == honest network (the baseline / normal case).
        self.fault_injector = fault_injector

        # Reproducible RNG. Never use the global `random` module here —
        # different runs would diverge and break experiment replication.
        self.rng = random.Random(seed)

        # Runtime state.
        self.nodes: dict[int, "Node"] = {}             # node_id -> Node, populated via register_node.
        self.message_log: list[Message] = []           # Full history; per-message inspection (Phase 5).
        self.round_stats = defaultdict(lambda: {        # Per-round counters (Phase 7 CSV columns).
            'sent': 0, 'delivered': 0, 'dropped': 0,
            'delayed': 0, 'replayed': 0, 'equivocated': 0,
        })
        self.next_message_id = 0

    # =========================
    # Node registration
    # =========================

    def register_node(self, node):
        """Attach a Node so the network can deliver messages to it by id."""
        self.nodes[node.node_id] = node

    # =========================
    # Latency sampling
    # =========================

    def sample_latency(self) -> float:
        """Gaussian latency sample, clipped at 0 to avoid negative delays."""
        raw = self.rng.gauss(self.latency_mean, self.latency_std)
        return max(0.0, raw)

    # =========================
    # Send / Broadcast
    # =========================

    def send_message(self, msg: Message) -> None:
        """
        Hand off a single message to the network.

        Plain method (no yield): timestamps, logs, increments counters,
        and spawns the _deliver process. Returns immediately so that
        broadcast() can dispatch many messages in zero simulated time.
        """
        msg.send_time = self.env.now
        self.message_log.append(msg)
        self.round_stats[msg.round_id]['sent'] += 1
        if self.fault_injector is None:
            self.env.process(self._deliver(msg))
            return
        
        result = self.fault_injector.on_send(msg)

        if result is None:
            self.round_stats[msg.round_id]['dropped'] +=1
            return
        
        for i, out_msg in enumerate(result):
            if i>0:
                out_msg.message_id = self._new_message_id()
                out_msg.send_time = self.env.now
                self.message_log.append(out_msg)
                self.round_stats[msg.round_id]['sent'] +=1
                if out_msg.fault_type == 'replay':
                    self.round_stats[msg.round_id]['replayed'] += 1
            
            if out_msg.fault_type == 'equivocation':
                self.round_stats[msg.round_id]['equivocated'] += 1
            self.env.process(self._deliver(out_msg))

    def broadcast(self, sender_id: int, msg_template: Message, receiver_ids: list[int]) -> None:
        """
        Send a copy of msg_template to each receiver.

        Each receiver gets an independent copy so per-message fields like
        delivery_time, message_id, and receiver_id can be set without
        clobbering siblings. dataclasses.replace gives us a cheap shallow
        copy with the overridden fields.
        """
        for r_id in receiver_ids:
            new_msg = dataclasses.replace(
                msg_template,
                receiver_id=r_id,
                message_id=self._new_message_id(),
            )
            self.send_message(new_msg)

    # =========================
    # Internal delivery process
    # =========================

    def _deliver(self, msg: Message):
        """
        SimPy process. The only method in this class that yields.

        Flow: sample latency -> yield timeout -> decide drop AFTER the
        timeout (drops are timestamped at the would-be arrival moment,
        matching the physics of in-flight packet loss) -> stamp
        delivery_time -> hand the message to the receiver node.
        """
        latency = self.sample_latency()

        if self.fault_injector is not None:
            extra = self.fault_injector.extra_latency(msg)
            if extra>0:
                latency += extra
                msg.fault_type = 'delay'
                self.round_stats[msg.round_id]['delayed'] +=1
        yield self.env.timeout(latency)

        if self.rng.random() < self.drop_rate:
            self.round_stats[msg.round_id]['dropped'] += 1
            return

        msg.delivery_time = self.env.now
        self.round_stats[msg.round_id]['delivered'] += 1
        self.nodes[msg.receiver_id].receive(msg)

    # =========================
    # Helpers
    # =========================

    def _new_message_id(self) -> int:
        """Monotonically increasing id, keeps every broadcast copy unique."""
        self.next_message_id += 1
        return self.next_message_id
