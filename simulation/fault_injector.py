"""
Byzantine fault injection module.

Sits between Node and SimPyNetwork. Two hooks let it rewrite the message flow:
  - on_send(msg)        -> decide whether / how the message enters delivery
                           (silent: drop, replay: clone, equivocation: fork content)
  - extra_latency(msg)  -> add network delay on top of the base latency
                           (delay attack)

The injector never yields — all timing comes from SimPy's network layer.
When fault_type == 'normal' (or sender is honest), every hook is a no-op,
so the injector doubles as the "null" baseline.
"""

import random, dataclasses
from typing import Any

from simulation.message import Message
from config import BYZANTINE_DELAY_MS, RANDOM_SEED, NUM_NODES


class FaultInjector:
    """Attacker module. Two hooks (on_send + extra_latency) cover all 4 fault types."""

    def __init__(
        self,
        fault_type: str = 'normal',
        byzantine_node_ids: set[int] | None = None,
        fault_intensity: float = 1.0,
        extra_delay_ms: float = BYZANTINE_DELAY_MS,
        seed: int = RANDOM_SEED,
        total_nodes: int = NUM_NODES
    ):
        self.fault_type = fault_type
        self.byzantine_ids = set(byzantine_node_ids or [])
        self.fault_intensity = fault_intensity
        self.extra_delay_ms = extra_delay_ms
        self.rng = random.Random(seed)
        self.total_nodes = total_nodes
        self.honest_ids = set(range(total_nodes)) - self.byzantine_ids

    # =========================
    # Hooks called by SimPyNetwork
    # =========================

    def on_send(self, msg: Message) -> list[Message] | None:
        """
        Called before a message enters the delivery pipeline.

        Returns:
          - [msg]               : send unchanged (honest path / pass-through)
          - [msg_a, msg_b, ...] : send these instead (replay, equivocation)
          - None                : drop the message (silent)
        """
        # Honest sender — pass through. (BFT-Simulator's fail-stop pattern.)
        if msg.sender_id not in self.byzantine_ids:
            return [msg]

        # Dispatch on fault_type. Stubs for Phase 4 incremental implementation.
        if self.fault_type == 'silent':
            return self._on_silent(msg)
        if self.fault_type == 'replay':
            return self._on_replay(msg)
        if self.fault_type == 'equivocation':
            return self._on_equivocation(msg)
        if self.fault_type == 'forgery':
            return self._on_forgery(msg)
        # 'normal' or 'delay': no rewrite, only timing.
        return [msg]

    def extra_latency(self, msg: Message) -> float:
        """Added on top of base network latency. 0 for honest / non-delay attacks."""
        if msg.sender_id in self.byzantine_ids and self.fault_type == 'delay':
            return self.extra_delay_ms * self.fault_intensity
        return 0.0

    # =========================
    # Fault implementations (to be filled in Phase 4 step-by-step)
    # =========================

    def _on_silent(self, msg: Message) -> list[Message] | None:
        # TODO Phase 4: drop with probability = fault_intensity
        if self.rng.random() < self.fault_intensity:
            msg.fault_type = 'silent'
            return None
        return [msg]

    def _on_replay(self, msg: Message) -> list[Message] | None:
        # TODO Phase 4: also emit a duplicate / old message
        msg.fault_type = 'replay'
        duplicate = dataclasses.replace(
            msg,
            message_id = 0,
            is_corrupt = True,
            fault_type = 'replay'
        )
        return [msg, duplicate]

    def _on_equivocation(self, msg: Message) -> list[Message] | None:
        # Phase 4: fork content based on receiver_id
        if msg.receiver_id % 2 == 0:
            return [msg]
        forked = dataclasses.replace(
            msg,
            message_id = 0,
            content = f'{msg.content}__forked',
            is_corrupt = True,
            fault_type = 'equivocation'
        )
        return [forked]
    
    def _on_forgery(self, msg: Message) -> list[Message] | None:
        if self.rng.random() >= self.fault_intensity:
            return [msg]

        candidates = self.honest_ids - set([msg.sender_id])

        if not candidates:
            return [msg]

        forged_node = self.rng.choice(sorted(candidates))

        forged = dataclasses.replace(
            msg,
            message_id = 0,
            sender_id = forged_node,
            is_corrupt = True,
            fault_type = 'forgery'
        )
        return [msg,forged]