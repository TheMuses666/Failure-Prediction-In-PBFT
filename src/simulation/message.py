"""
Message data class.

A pure data container exchanged between nodes via the SimPy network layer.
Has no behaviour and no dependency on SimPy — Message is the data,
SimPyNetwork is the actor that moves it through simulated time.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    # --- Required at creation time (filled by the sender / protocol layer) ---
    message_id: int          # Unique per network message; assigned by SimPyNetwork.
    message_type: str        # 'pre_prepare' | 'prepare' | 'commit' | 'reply'.
    sender_id: int           # Node id of the sender.
    receiver_id: int         # Node id of the intended receiver.
    round_id: int            # PBFT consensus round (sequence number).
    content: Any             # Proposal payload; for equivocation, two messages with
                             # the same (round_id, sender_id) but different content
                             # reveal the attack.

    # --- Filled by the network layer ---
    send_time: float | None = None      # env.now at the moment send_message() is called.
    delivery_time: float | None = None  # env.now when the receiver is handed the message.
                                        # None means the message was dropped or is still
                                        # in flight.

    # --- Filled by the fault injector (Phase 4) ---
    fault_type: str | None = None       # Type of Byzantine fault applied to this message.
    is_corrupt: bool = False            # True if the content was tampered with.
