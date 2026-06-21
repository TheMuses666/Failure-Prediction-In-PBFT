from config import NORMAL_LATENCY_THRESHOLD_MAX,DROP_RATE_WARNING,MESSAGE_CONSISTENCY_WARNING

def generate_label(round_result, features):
    honest_nodes_commit = len(set(round_result['committed_node_ids']) - set(round_result['byzantine_node_ids']))
    if round_result['timeout'] or not round_result['success'] or honest_nodes_commit < round_result['quorum_size']:
        return 2
    
    if (features['message_latency'] >= NORMAL_LATENCY_THRESHOLD_MAX
        or features['message_drop_rate'] >= DROP_RATE_WARNING
        or features['message_consistency'] < MESSAGE_CONSISTENCY_WARNING
        or round_result['forged'] > 0
        or round_result['same_round_replayed'] > 0
        or round_result['stale_replayed'] > 0
    ):
        return 1
    
    return 0