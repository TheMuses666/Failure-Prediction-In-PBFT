import torch
from torch_geometric.data import Data
from config import MESSAGE_TYPE_TO_ID

def build_graph(raw: dict, label:int) -> Data:
    nodes = raw['_node']
    round_id = raw['_round_id']
    primary_id = raw['_primary_id']
    commited_node_ids = set(raw['_committed_node_ids'])

    node_features = []
    for n in nodes:
        is_primary = 1 if n['node_id'] == primary_id else 0
        has_committed = 1 if n['node_id'] in commited_node_ids else 0

        own_prepare_votes = sum(len(s) for s in n.prepare_log.get(round_id, {}).values())
        own_commit_votes = sum(len(s) for s in n.commit_log.get(round_id, {}).values())

        first_response = n.first_response_time.get(round_id, -1.0)

        phases = n.phase_time.get(round_id, {})
        if 'commit' in phases and 'prepare' in phases:
            phase_duration = phases['commit'] - phases['prepare']
        else:
            phase_duration = -1.0

        node_features.append([
            is_primary,
            has_committed,
            float(own_prepare_votes),
            float(own_commit_votes),
            float(first_response),
            float(phase_duration)
        ])
