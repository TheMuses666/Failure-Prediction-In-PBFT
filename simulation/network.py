import time
from config import NUM_BYZANTINE_NODES, CONSENSUS_TIMEOUT_MS
from simulation.pbft import PBFT_protocol

class Network():
    def __init__(self, nodes):
        self.nodes = nodes
        self.primary = nodes[0]
        self.round_metrics = []
        self.pbft = PBFT_protocol()

    def run_round(self, round_id):

        # 1. strat time
        start_time = time.time()

        # 2. pre-prepare 
        self.pbft.pre_prepare(self.primary, self.nodes, round_id)

        # 3. Prepare
        self.pbft.prepare(self.primary, self.nodes,  round_id)

        # 4. Commit
        self.pbft.commit(self.nodes, round_id)


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
            timeout=timeout,
            success=success,
            success_count=success_count
        )

        self.reset_nodes()
        return metrics
        

    def reset_nodes(self):
        for node in self.nodes:
            node.message_log = []
            node.prepare_log = {}
            node.commit_log = {}
            node.current_phase = None

    def extract_round_metrics(self, round_id, duration_ms, timeout, success, success_count):
        return {
            "round_id": round_id,
            "success": success,
            "duration_ms": duration_ms,
            "timeout": timeout,
            "success_count": success_count,

            # later feature columns
            "message_latency": None,
            "message_drop_rate": None,
            "propagation_pattern": None,
            "consensus_agreement_time": duration_ms,
            "phase_completion_time": None,
            "timeout_frequency": int(timeout),
            "leader_change_frequency": 0,
            "response_time": duration_ms,
            "voting_consistency": None,
            "message_consistency": None,
            "vote_deviation": None,
        }