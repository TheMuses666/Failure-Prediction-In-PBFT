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


def compute_features_at_time(round_result: dict, cutoff_ms: float) -> dict:
    """
    重算所有 13 个特征，只使用 t <= cutoff_ms 时可获得的信息。
    如果 cutoff_ms >= 整个轮次结束，等价于 extract_features(round_result)。
    """
    paired = list(zip(round_result['delivery_times'], round_result['latencies']))
    filtered_latencies = [lat for dt, lat in paired if dt <= cutoff_ms]
    filtered_delivery_times = [dt for dt in round_result['delivery_times'] if dt <= cutoff_ms]   
    prepare_msgs = [m for m in round_result['prepare_messages']
                    if m.delivery_time is not None and m.delivery_time <= cutoff_ms]
    commit_msgs  = [m for m in round_result['commit_messages']
                    if m.delivery_time is not None and m.delivery_time <= cutoff_ms]
    
    all_messages = round_result['all_messages']

   # Message Latency
    message_latency = float(np.mean(filtered_latencies)) if filtered_latencies else 0.0 

    # Message Drop Rate
    sent_by_cutoff, dropped_by_cutoff = 0, 0
    for m in all_messages:
       if m.send_time <= cutoff_ms:
          sent_by_cutoff +=1
          if m.delivery_time is None:
             dropped_by_cutoff +=1
             
    message_drop_rate = dropped_by_cutoff / sent_by_cutoff if sent_by_cutoff > 0 else 0.0

    # Propagation Pattern
    propagation_pattern = float(np.std(filtered_delivery_times)) if filtered_delivery_times else 0.0
    
    # Consensus Agreement Time
    # 特征 4: consensus_agreement_time
    end_t = round_result['consensus_end_time']
    if end_t is not None and end_t <= cutoff_ms:
        effective_end = end_t
    elif cutoff_ms < CONSENSUS_TIMEOUT_MS:
        effective_end = cutoff_ms
    else:
        effective_end = CONSENSUS_TIMEOUT_MS

    consensus_agreement_time = effective_end - round_result['round_start_time']

    # Phase Completion
    phase_spans = []
    for phase_times in round_result['per_node_phase_times']:
        if ('commit' in phase_times 
                and 'prepare' in phase_times 
                and phase_times['commit'] <= cutoff_ms):
            phase_spans.append(phase_times['commit'] - phase_times['prepare'])

    phase_completion_time = float(np.mean(phase_spans)) if phase_spans else 0.0

    # Timeout Frequency
    timeout_frequency = 1 if (cutoff_ms >= CONSENSUS_TIMEOUT_MS and round_result['timeout']) else 0

    # Response Time
    first_arrival_nodes = {}
    for m in prepare_msgs:    # ← 唯一改动：用 filtered 的 list
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
    committed_by_cutoff = 0
    for phase_times in round_result['per_node_phase_times']:
        if 'commit' in phase_times and phase_times['commit'] <= cutoff_ms:
            committed_by_cutoff += 1

    voting_consistency = committed_by_cutoff / round_result['total_nodes']

    # Message Consistency
    if commit_msgs:
       contents = [m.content for m in commit_msgs]
       most_common_count = max(Counter(contents).values())
       message_consistency = most_common_count / len(contents)
    else:
       message_consistency = 0.0

    # Vote Deviation

    if cutoff_ms >= CONSENSUS_TIMEOUT_MS:
      # 轮次已完成，直接用记录的 per_node_commit_log（包含 silent 节点的本地 self-vote）
      commit_counts_per_node = []
      for log in round_result['per_node_commit_log']:
          total_votes = sum(len(senders) for senders in log.values())
          commit_counts_per_node.append(total_votes)
    else:
       # cutoff 在轮次进行中——从 commit_msgs 反推（近似）
       per_node_log_at_cutoff = defaultdict(lambda: defaultdict(set))
       for m in commit_msgs:
           per_node_log_at_cutoff[m.receiver_id][m.content].add(m.sender_id)
           per_node_log_at_cutoff[m.sender_id][m.content].add(m.sender_id)   # self-vote for senders
    
       commit_counts_per_node = []
       for nid in range(round_result['total_nodes']):
           log = per_node_log_at_cutoff.get(nid, {})
           total_votes = sum(len(senders) for senders in log.values())
           commit_counts_per_node.append(total_votes)

    vote_deviation = float(np.std(commit_counts_per_node)) if commit_counts_per_node else 0.0

    # Quorum Margin
    quorum_margin = voting_consistency - (round_result['quorum_size'] / round_result['total_nodes'])

    # Prepare Count STD
    prepare_count = Counter()
    for m in prepare_msgs:   # ← 唯一改动
        prepare_count[m.receiver_id] += 1
    for nid in range(round_result['total_nodes']):
      if nid not in prepare_count:
          prepare_count[nid] = 0
    prepare_count_std = float(np.std(list(prepare_count.values())))


    
    return {
        'message_latency': message_latency,
        'message_drop_rate': message_drop_rate,
        'propagation_pattern': propagation_pattern,
        'consensus_agreement_time': consensus_agreement_time,
        'phase_completion_time': phase_completion_time,
        'timeout_frequency': timeout_frequency,
        'leader_change_frequency': 0,
        'response_time': response_time,
        'voting_consistency': voting_consistency,
        'message_consistency': message_consistency,
        'vote_deviation': vote_deviation,
        'quorum_margin': quorum_margin,
        'prepare_count_std': prepare_count_std,
    }