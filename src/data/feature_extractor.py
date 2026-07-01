import numpy as np
from collections import Counter, defaultdict
from config import CONSENSUS_TIMEOUT_MS
def extract_features(round_result: dict) ->dict:

    # Message Latency
    latencies = round_result['latencies']
    if len(latencies) != 0:
      message_latency = float(np.mean(latencies))
    else:
      message_latency = 0.0
    
    # Message Drop Rate
    sent = round_result['sent']
    if sent > 0:
       message_drop_rate = round_result['dropped'] / sent
    else:
       message_drop_rate = 0.0

    # Propagation Pattern
    delivery_times = round_result['delivery_times']
    if len(delivery_times) != 0:
       propagation_pattern = float(np.std(delivery_times))
    else:
       propagation_pattern = 0.0

    # Consensus Agreement Time
    consensus_end_time = round_result['consensus_end_time'] if round_result['consensus_end_time'] is not None else CONSENSUS_TIMEOUT_MS
    consensus_agreement_time = consensus_end_time - round_result['round_start_time']

    # Phase Completion Time
    phase_spans = []
    for each_phase_time in round_result['per_node_phase_times']:
       if 'commit' in each_phase_time and 'prepare' in each_phase_time:
          phase_spans.append(each_phase_time['commit'] - each_phase_time['prepare'])

    if len(phase_spans) != 0:
       phase_completion_time = float(np.mean(phase_spans))
    else:
       phase_completion_time = 0.0

    # Timeout Frequency
    timeout_frequency = int(round_result['timeout'])


    # Leader Change Frequency / View Change
    leader_change_frequency = 0

    # Response Time
    first_arrival_nodes = {}
    for m in round_result['prepare_messages']:
       if m.sender_id not in first_arrival_nodes or m.delivery_time < first_arrival_nodes[m.sender_id]:
          first_arrival_nodes[m.sender_id] = m.delivery_time

    response_samples = []
    for nid in range(round_result['total_nodes']):
        if nid == round_result['primary_id']:
           continue
        if nid in first_arrival_nodes:
           response_samples.append(first_arrival_nodes[nid])
        else:
           response_samples.append(CONSENSUS_TIMEOUT_MS)
    
    response_time = float(np.mean(response_samples)) if response_samples else 0.0       

    # Voting Consistency
    voting_consistency = len(round_result['committed_node_ids']) / round_result['total_nodes']

   # Quorum Margin
    quorum_margin = voting_consistency - (round_result['quorum_size'] / round_result['total_nodes'])

    # Prepare_count_std
    prepare_count = Counter()
    for m in round_result['prepare_messages']:
      prepare_count[m.receiver_id] += 1
    for nid in range(round_result['total_nodes']):
      if nid not in prepare_count:
         prepare_count[nid] = 0
    prepare_count_std = float(np.std(list(prepare_count.values())))

    # Message Consistency
    commit_msgs = round_result['commit_messages']
    if len(commit_msgs) != 0:
       contents = [m.content for m in commit_msgs]
       most_comment_counts = max(Counter(contents).values())
       message_consistency = most_comment_counts / len(contents)
    else:
       message_consistency = 0.0

    # Voting Deviation
    commit_counts_per_node = []

    for log in round_result['per_node_commit_log']:
       total_votes = sum(len(senders) for senders in log.values())
       commit_counts_per_node.append(total_votes)

    if len(commit_counts_per_node) != 0:
       vote_deviation = float(np.std(commit_counts_per_node))
    else:
       vote_deviation = 0.0

    return {
        # Features feed to ML
        'message_latency': message_latency,
        'message_drop_rate': message_drop_rate,
        'propagation_pattern': propagation_pattern,
        'consensus_agreement_time': consensus_agreement_time,
        'phase_completion_time': phase_completion_time,
        'timeout_frequency': timeout_frequency,
        'leader_change_frequency': leader_change_frequency,
        'response_time': response_time,
        'voting_consistency': voting_consistency,
        'message_consistency': message_consistency,
        'vote_deviation': vote_deviation,
        'quorum_margin': quorum_margin,
        'prepare_count_std': prepare_count_std,

        # Auxiliary Counters
        'forged': round_result['forged'],
        'replayed': round_result['replayed'],
        'same_round_replayed': round_result['same_round_replayed'],
        'stale_replayed': round_result['stale_replayed'],
        'equivocated': round_result['equivocated'],
        'delayed': round_result['delayed'],
        'strict_round_validation': round_result['strict_round_validation'],
        'silent_mode':        round_result['silent_mode'],
        'delay_probability':  round_result['delay_probability'],
        'delay_distribution': round_result['delay_distribution'],
    }
