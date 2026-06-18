import numpy as np
from config import NUM_NODES
def extract_features(round_result):

    prepare_counts = round_result.get('prepare_counts', [])
    commit_counts = round_result.get('commit_counts', [])

    all_message_counts = prepare_counts + commit_counts

    # Consensus Agree TIme
    consensus_agree_time = round_result['duration_ms']

    # voting consistency
    voting_consistency = round_result['success_count'] / NUM_NODES

    # message_latency, propagation_pattern
    message_latency = round_result.get("pre_prepare_time", 0)
    propagation_pattern = float(np.std(all_message_counts)) if all_message_counts else 0.0

    # Message Drop Rate
    message_drop_rate = round_result.get("message_drop_rate", 0)

    # Phase Completion Time
    phase_completion_time = (
        round_result.get("prepare_time", 0)
        + round_result.get("commit_time", 0)
    )

    # Timeout frequency
    timeout_frequency = int(round_result["timeout"])
    leader_change_frequency = 0

    # Response Time
    response_time = float(np.mean(all_message_counts)) if all_message_counts else 0.0

    # Message Consistency
    if commit_counts:
        message_consistency = max(commit_counts) / (NUM_NODES - 1)
    else:
        message_consistency = 0.0

    # Voting Deviation
    vote_deviation = float(np.std(commit_counts)) if commit_counts else 0.0

    return {
            'message_latency': message_latency,
            'message_drop_rate': message_drop_rate,
            'propagation_pattern': propagation_pattern,
            'consensus_agreement_time': consensus_agree_time,
            'phase_completion_time': phase_completion_time,
            'timeout_frequency': timeout_frequency,
            'leader_change_frequency': leader_change_frequency,
            'response_time': response_time,
            'voting_consistency': voting_consistency,
            'message_consistency': message_consistency,
            'vote_deviation': vote_deviation,
    }
