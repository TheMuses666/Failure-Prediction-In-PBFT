"""
PBFT round orchestrator.

Wires together SimPyNetwork + Node into one full consensus round.
Uses a simpy.Event to wait for either commit-quorum success or timeout.
"""

import simpy

from simulation.simpy_network import SimPyNetwork
from simulation.node import Node
from config import NUM_NODES, CONSENSUS_TIMEOUT_MS, RANDOM_SEED

def _wait_for_round(env, commit_event, timeout_ms):
    """
    SimPy process. Yields until either commit succeeds or the timeout fires.

    The caller doesn't read a return value — after env.run() finishes,
    inspect commit_event.triggered to know what happened.
    """
    timeout_event = env.timeout(timeout_ms)
    yield env.any_of([commit_event, timeout_event])

def run_pbft_round(
        round_id:int,
        fault_type: str='normal',
        byzantine_node_ids: list[int] | None=None,
        total_nodes:int=NUM_NODES,
        timeout_ms: float=CONSENSUS_TIMEOUT_MS,
        seed: int=RANDOM_SEED
) -> dict:
    
    # Set up environment and network
    env = simpy.Environment()
    net = SimPyNetwork(env, seed=seed)

    # Nodes
    nodes = []
    byzantine_set = set(byzantine_node_ids or [])
    
    for i in range(total_nodes):
        is_byz = i in byzantine_set
        n = Node(
            node_id=i,
            network=net,
            is_byzantine=is_byz,
            fault_type=fault_type if is_byz else None,
            total_nodes=total_nodes
        )
        nodes.append(n)
        net.register_node(n)

    # Primary node
    primary_id = round_id % total_nodes
    primary = nodes[primary_id]
    quorum_size = nodes[0].quorum_size

    # Callback
    committed_nodes_set: set[int] = set()
    final_event = env.event()

    def on_commit(node_id:int) -> None:
        committed_nodes_set.add(node_id)
        if len(committed_nodes_set) == quorum_size and not final_event.triggered:
            final_event.succeed()

    for n in nodes:
        n.set_commit_callback(round_id, on_commit)

    #
    env.process(_wait_for_round(env, final_event, timeout_ms))
    primary.propose(round_id, content=f"req_{round_id}")

    env.run()

    commit_times = [n.phase_times[round_id].get('commit') for n in nodes if 'commit' in n.phase_times[round_id]]
    first_commit_time = min(commit_times) if commit_times else None

    return {
        'round_id': round_id,
        'fault_type': fault_type,
        'byzantine_node_ids': sorted(byzantine_set),
        'primary_id': primary_id,
        'success': final_event.triggered,
        'timeout': not final_event.triggered,
        'consensus_end_time': first_commit_time,
        'simulation_end_time': env.now(),
        'committed_nodes_count': len(committed_nodes_set),
        'committed_node_ids': sorted(committed_nodes_set),
        '_nodes': nodes,
        '_network': net,
    }

