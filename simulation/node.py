"""
Event-driven PBFT replica.

A Node is a passive state machine. It does NOT own a SimPy process and
never yields — every action runs to completion in zero simulated time
when the network calls receive(). The only thing that consumes simulated
time is the underlying _deliver process in SimPyNetwork.

PBFT phases tracked per round:
  pre_prepare -> prepare -> commit -> (reply, out of scope for Phase 2)

All per-round state is keyed by round_id so Phase 5 feature extraction
can pull a single round's data without filtering global logs.
"""

from collections import defaultdict
from typing import Any, Callable

from simulation.message import Message
from config import NUM_NODES


class Node:
    """PBFT replica — event-driven state machine."""

    def __init__(
        self,
        node_id: int,
        network,                              # SimPyNetwork (avoid the import to dodge cycles)
        is_byzantine: bool = False,
        fault_type: str | None = None,
        total_nodes: int = NUM_NODES,
    ):
        # --- identity ---
        self.node_id = node_id
        self.network = network
        self.is_byzantine = is_byzantine
        self.fault_type = fault_type            # Set by Phase 4 fault injector; None for honest nodes.

        # --- protocol constants ---
        # PBFT tolerates up to f Byzantine nodes when n >= 3f + 1.
        # Quorum size 2f + 1 guarantees any two quorums intersect in at
        # least one honest node (the safety argument behind two voting rounds).
        self.total_nodes = total_nodes
        self.f = (total_nodes - 1) // 3
        self.quorum_size = 2 * self.f + 1

        # --- per-round state ---
        # All dicts are keyed by round_id so Phase 5 can pull one round
        # of data without scanning a global log.
        self.received_messages: dict[int, list[Message]] = defaultdict(list)

        # round -> content -> set of sender_ids.
        # The inner key being `content` (not message_id) is what lets us
        # detect equivocation later: two contents in the same round means
        # the primary sent conflicting proposals.
        # set() (not list) prevents one sender's repeated message from
        # inflating the count past the quorum threshold.
        self.prepare_log: dict[int, dict[Any, set[int]]] = defaultdict(lambda: defaultdict(set))
        self.commit_log:  dict[int, dict[Any, set[int]]] = defaultdict(lambda: defaultdict(set))

        # round -> {'pre_prepare': t, 'prepare': t, 'commit': t}. Phase 5 derives
        # phase_completion_time = commit_t - pre_prepare_t from this.
        self.phase_times: dict[int, dict[str, float]]    = defaultdict(dict)

        # Set, not int, so membership is O(1) and the round count is len(...).
        self.committed_rounds: set[int]                  = set()

        # Time this node first emitted a prepare for the round (its reaction
        # latency). Phase 5 averages this across nodes for the response_time
        # feature; Byzantine 'delay' nodes are expected to stand out here.
        self.first_response_time: dict[int, float]       = {}

        # round_id -> simpy.Event, fired the moment this node first reaches commit quorum.
        # Set by the orchestrator (pbft.run_pbft_round) before the round starts.
        self.commit_callbacks: dict[int, Callable[[int], None]] = {}

    def set_commit_callback(self, round_id: int, callback) -> None:
        """Orchestrator hands us the event we should fire when this round commits."""
        self.commit_callbacks[round_id] = callback

    # =========================
    # Message reception
    # =========================

    def receive(self, msg: Message) -> None:
        """Entry point called by SimPyNetwork._deliver. Plain method (no yield)."""
        self.received_messages[msg.round_id].append(msg)
        if msg.message_type == 'pre_prepare':
            self._handle_pre_prepare(msg)
        elif msg.message_type == 'prepare':
            self._handle_prepare(msg)
        elif msg.message_type == 'commit':
            self._handle_commit(msg)
        else:
            raise ValueError(f"Unknown message type: {msg.message_type}")

    def _handle_pre_prepare(self, msg: Message) -> None:
        # Record entry into the pre_prepare phase and immediately answer
        # with a prepare broadcast. There is no validation step in this
        # Phase 2 implementation — content is accepted as-is.
        self.phase_times[msg.round_id]['pre_prepare'] = self.network.env.now
        self._broadcast_prepare(msg.round_id, msg.content)

    def _handle_prepare(self, msg: Message) -> None:
        self.prepare_log[msg.round_id][msg.content].add(msg.sender_id)
        # `==` not `>=`: trigger the commit broadcast exactly once, the
        # instant we cross the threshold. Using `>=` would re-broadcast
        # on every subsequent prepare that arrives.
        if len(self.prepare_log[msg.round_id][msg.content]) == self.quorum_size:
            self.phase_times[msg.round_id]['prepare'] = self.network.env.now
            self._broadcast_commit(msg.round_id, msg.content)

    def _handle_commit(self, msg: Message) -> None:
        self.commit_log[msg.round_id][msg.content].add(msg.sender_id)
        if len(self.commit_log[msg.round_id][msg.content]) == self.quorum_size:
            self.committed_rounds.add(msg.round_id)
            self.phase_times[msg.round_id]['commit'] = self.network.env.now
            # Notify orchestrator. `triggered` guards against firing twice when
            # other nodes also cross the threshold (Event.succeed raises otherwise).
            callback = self.commit_callbacks.get(msg.round_id)
            if callback is not None:
                callback(self.node_id)

    # =========================
    # Broadcasting helpers
    # =========================

    def _broadcast_prepare(self, round_id: int, content: Any) -> None:
        # first_response_time is the moment this node first reacts to the
        # round; only the first prepare counts, so guard with a membership check.
        if round_id not in self.first_response_time:
            self.first_response_time[round_id] = self.network.env.now

        # Self-vote: count our own prepare locally instead of looping it
        # through the network. Saves one delivery process per round and
        # avoids the case where a self-message gets randomly dropped.
        self.prepare_log[round_id][content].add(self.node_id)

        message_template = Message(
            message_id=0,                       # Overwritten per-receiver by broadcast().
            message_type='prepare',
            sender_id=self.node_id,
            receiver_id=-1,                     # Overwritten per-receiver by broadcast().
            round_id=round_id,
            content=content,
        )
        receiver_ids = [i for i in range(self.total_nodes) if i != self.node_id]
        self.network.broadcast(self.node_id, message_template, receiver_ids)

    def _broadcast_commit(self, round_id: int, content: Any) -> None:
        # Self-vote in the commit phase, same reasoning as in prepare.
        self.commit_log[round_id][content].add(self.node_id)

        message_template = Message(
            message_id=0,
            message_type='commit',
            sender_id=self.node_id,
            receiver_id=-1,
            round_id=round_id,
            content=content,
        )
        receiver_ids = [i for i in range(self.total_nodes) if i != self.node_id]
        self.network.broadcast(self.node_id, message_template, receiver_ids)

    def propose(self, round_id: int, content: Any) -> None:
        """Primary entry point. Broadcasts pre_prepare to all backups."""
        template = Message(
            message_id=0,
            message_type='pre_prepare',
            sender_id=self.node_id,
            receiver_id=-1,
            round_id=round_id,
            content=content,
        )
        receivers = [i for i in range(self.total_nodes) if i != self.node_id]
        self.network.broadcast(self.node_id, template, receivers)

    # =========================
    # Queries
    # =========================

    def has_committed(self, round_id: int) -> bool:
        return round_id in self.committed_rounds

    def has_prepare_quorum(self, round_id: int, content: Any) -> bool:
        return len(self.prepare_log[round_id][content]) >= self.quorum_size

    def has_commit_quorum(self, round_id: int, content: Any) -> bool:
        return len(self.commit_log[round_id][content]) >= self.quorum_size
