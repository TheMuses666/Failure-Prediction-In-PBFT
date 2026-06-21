def build_round_result(raw: dict) -> dict:
    nodes = raw['_nodes']
    net = raw['_network']
    round_id = raw['round_id']
    injector = net.fault_injector

    stats = net.round_stats[round_id]
    this_round_msgs = [m for m in net.message_log if m.round_id == round_id]
    delivered_msgs = [m for m in this_round_msgs if m.delivery_time is not None]

    return {
        # Raw data
        'round_id': round_id,
        'fault_type': raw['fault_type'],
        'success': raw['success'],
        'timeout': raw['timeout'],
        'byzantine_node_ids': raw['byzantine_node_ids'],
        'total_nodes': len(nodes),
        'primary_id': round_id % len(nodes),
        'quorum_size': nodes[0].quorum_size,
        'strict_round_validation': raw['strict_round_validation'],

        # Timeline
        'round_start_time': 0.0,
        'round_end_time': raw['simulation_end_time'],
        'consensus_end_time': raw['consensus_end_time'],

        # Network-layer Counts
        'sent': stats['sent'],
        'delivered': stats['delivered'],
        'dropped': stats['dropped'],
        'delayed': stats['delayed'],
        'replayed': stats['replayed'],
        'same_round_replayed': stats['same_round_replayed'],
        'stale_replayed': stats['stale_replayed'],
        'equivocated': stats['equivocated'],
        'forged': stats['forged'],

        # Fault injector configuration (auxiliary for Phase 11 ablation)
        'silent_mode':        injector.silent_mode        if injector else 'all',
        'delay_probability':  injector.delay_probability  if injector else 1.0,
        'delay_distribution': injector.delay_distribution if injector else 'gaussian',

        # Feature Calculation
        'latencies': [m.delivery_time - m.send_time for m in delivered_msgs],
        'delivery_times': [m.delivery_time for m in delivered_msgs],
        'commit_messages': [m for m in delivered_msgs if m.message_type == 'commit'],
        'prepare_messages': [m for m in delivered_msgs if m.message_type == 'prepare'],

        # Node
        'per_node_phase_times': [n.phase_times.get(round_id, {}) for n in nodes],
        'per_node_first_response': [n.first_response_time.get(round_id) for n in nodes],
        'per_node_commit_log': [n.commit_log.get(round_id, {}) for n in nodes],

        'committed_node_ids': raw['committed_node_ids']
    }