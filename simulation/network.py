import time
from config import NUM_BYZANTINE_NODES, CONSENSUS_TIMEOUT_MS
from simulation.pbft import PBFT_protocol
from collection.feature_extractor import extract_features
from collection.label_generator import generate_label

class Network():
    def __init__(self, nodes):
        self.nodes = nodes
        self.primary = nodes[0]
        self.round_metrics = []
        self.pbft = PBFT_protocol()

    def run_round(self, round_id):

        # 1. Total strat time
        start_time = time.time()

        # 2. Pre-prepare 
        phase_start = time.time()
        self.pbft.pre_prepare(self.primary, self.nodes, round_id)
        pre_prepare_time = (time.time() - phase_start) * 1000

        # 3. Prepare
        phase_start = time.time()
        self.pbft.prepare(self.primary, self.nodes,  round_id)
        prepare_time = (time.time() - phase_start) * 1000

        # 4. Commit
        phase_start = time.time()
        self.pbft.commit(self.nodes, round_id)
        commit_time = (time.time() - phase_start) * 1000


        # 5. Censensus result

        quorum = 2* NUM_BYZANTINE_NODES + 1
        success_count = self.pbft.check_consensus(self.nodes, round_id, quorum)

        # 6. time cost
        duration_ms = (time.time() - start_time) * 1000

        # Wether timeout
        timeout = duration_ms > CONSENSUS_TIMEOUT_MS

        # Wether Consensus Success
        success = success_count >= quorum and not timeout


        metrics = self.extract_round_metrics(
            round_id=round_id,
            duration_ms=duration_ms,
            pre_prepare_time = pre_prepare_time,
            prepare_time = prepare_time,
            commit_time = commit_time,
            timeout=timeout,
            success=success,
            success_count=success_count
        )

        features = extract_features(metrics)
        label = generate_label(metrics)

        row = {
            **metrics,
            **features,
           "label": label
        }

        self.reset_nodes()
        return row
        

    def reset_nodes(self):
        for node in self.nodes:
            node.message_log = []
            node.prepare_log = {}
            node.commit_log = {}
            node.current_phase = None

    def extract_round_metrics(self, round_id, duration_ms, pre_prepare_time, prepare_time, commit_time, timeout, success, success_count):
 
        total_messages = sum(len(node.message_log) for node in self.nodes)
        prepare_counts = [len(node.prepare_log.get(round_id, [])) for node in self.nodes]
        commit_counts = [len(node.commit_log.get(round_id, [])) for node in self.nodes]

        expected_pre_prepare_message = len(self.nodes) - 1
        expected_prepare_message = (len(self.nodes)-1) **2
        expected_commit_message = (len(self.nodes)) * (len(self.nodes)-1)
        expected_messages = expected_prepare_message + expected_commit_message + expected_pre_prepare_message

        delivered_messages = total_messages
        dropped_messages = max(expected_messages - delivered_messages, 0)
        message_drop_rate = dropped_messages / expected_messages if expected_messages else 0
 
        return {
            "round_id": round_id,
            "success": success,
            "duration_ms": duration_ms,
            "pre_prepare_time": pre_prepare_time,
            "prepare_time": prepare_time,
            "commit_time": commit_time,
            "timeout": timeout,
            "success_count": success_count,
            "total_messages": total_messages,
            "expected_messages": expected_messages,
            "delivered_messages": delivered_messages,
            "dropped_messages": dropped_messages,
            "message_drop_rate": message_drop_rate,
            "prepare_counts": prepare_counts,
            "commit_counts": commit_counts,
        }