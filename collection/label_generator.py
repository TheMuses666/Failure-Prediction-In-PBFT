from config import NORMAL_LATENCY_THRESHOLD_MAX

def generate_label(round_result):
    if round_result['timeout'] or not round_result['success']:
        
        return 2
    
    if round_result['duration_ms'] >= NORMAL_LATENCY_THRESHOLD_MAX:
        return 1
    
    return 0