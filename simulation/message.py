from dataclasses import dataclass
from typing import Any

@dataclass
class Message:
    message_id: int
    message_type: str
    sender_id: int
    receiver_id: int
    round_id: int
    content: Any
    send_time: float | None = None
    delivery_time: float | None = None
    fault_type: str | None = None
    is_corrupt: bool = False