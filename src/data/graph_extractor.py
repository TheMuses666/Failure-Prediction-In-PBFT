import torch
from torch_geometric.data import Data

from config import CONSENSUS_TIMEOUT_MS, MESSAGE_TYPE_TO_ID


MESSAGE_TYPES = tuple(MESSAGE_TYPE_TO_ID.keys())


def build_graph(raw: dict, label: int) -> Data:
    nodes = raw['_nodes']
    net = raw['_network']
    round_id = raw['round_id']
    primary_id = raw['primary_id']
    total_nodes = len(nodes)
    quorum_size = nodes[0].quorum_size

    node_features = []
    for node in nodes:
        prepare_counts = [
            len(voters)
            for voters in node.prepare_log.get(round_id, {}).values()
        ]
        commit_counts = [
            len(voters)
            for voters in node.commit_log.get(round_id, {}).values()
        ]

        max_prepare_votes = max(prepare_counts, default=0)
        max_commit_votes = max(commit_counts, default=0)
        total_prepare_votes = sum(prepare_counts)
        total_commit_votes = sum(commit_counts)

        first_response = node.first_response_time.get(round_id)
        has_first_response = first_response is not None
        first_response_norm = (
            first_response / CONSENSUS_TIMEOUT_MS if has_first_response else 0.0
        )

        phases = node.phase_times.get(round_id, {})
        has_phase_duration = 'commit' in phases and 'prepare' in phases
        phase_duration_norm = (
            (phases['commit'] - phases['prepare']) / CONSENSUS_TIMEOUT_MS
            if has_phase_duration else 0.0
        )

        node_features.append([
            1.0 if node.node_id == primary_id else 0.0,
            max_prepare_votes / quorum_size,
            total_prepare_votes / (total_nodes * total_nodes),
            max_commit_votes / quorum_size,
            total_commit_votes / (total_nodes * total_nodes),
            1.0 if has_first_response else 0.0,
            float(first_response_norm),
            1.0 if has_phase_duration else 0.0,
            float(phase_duration_norm),
        ])

    edge_index = []
    edge_features = []
    for message in net.message_log:
        if message.round_id != round_id:
            continue

        edge_index.append([message.sender_id, message.receiver_id])

        is_delivered = message.delivery_time is not None
        latency = (
            message.delivery_time - message.send_time
            if is_delivered else 0.0
        )
        message_type_one_hot = [
            1.0 if message.message_type == message_type else 0.0
            for message_type in MESSAGE_TYPES
        ]

        edge_features.append(message_type_one_hot + [
            latency / CONSENSUS_TIMEOUT_MS,
            1.0 if is_delivered else 0.0,
            1.0 if message.sender_id == primary_id else 0.0,
            1.0 if message.receiver_id == primary_id else 0.0,
        ])

    x = torch.tensor(node_features, dtype=torch.float)
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_features, dtype=torch.float)
    y = torch.tensor([label], dtype=torch.long)

    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
