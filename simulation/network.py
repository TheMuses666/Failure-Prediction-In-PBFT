import time
from config import NUM_BYZANTINE_NODES, CONSENSUS_TIMEOUT_MS

class Network():
    def __init__(self, nodes):
        self.nodes = nodes
        self.primary = nodes[0]
        self.round_metrics = []

    def run_round(self, round_id):

        # 1. strat time
        start_time = time.time()

        # 2. pre-prepare 
        message = {
            'type': 'pre_prepare',
            'sender_id': self.primary.node_id,
            'round_id': round_id,
            'content': f'request_{round_id}'  
        }

        self.primary.broadcast(self.nodes, message)

        # 3. Prepare

        for node in self.nodes:
            if node.node_id != self.primary.node_id:
                prepare_message = {
                    'type': 'prepare',
                    'sender_id': node.node_id,
                    'round_id': round_id,
                    'content': f'request_{round_id}'  
                }
                node.broadcast(self.nodes, prepare_message)

        # 4. Commit

        for node in self.nodes:
            commit_message = {
                'type': 'commit',
                'sender_id': node.node_id,
                'round_id': round_id,
                'content': f'request_{round_id}'  
            }
            node.broadcast(self.nodes, commit_message)

        # 5. Censensus result

        quorum = 2* NUM_BYZANTINE_NODES + 1
        success_count = 0
        for node in self.nodes:
            commits = node.commit_log.get(round_id, [])
            if len(commits) >= quorum:
                success_count +=1

        # 6. time cost
        duration_ms = (time.time() - start_time) * 1000

        # Wether timeout
        timeout = duration_ms > CONSENSUS_TIMEOUT_MS

        # Wether Consensus Success
        success = success_count >= quorum and not timeout


    
        return {
            'round_id': round_id,
            'success': success,
            'duration_ms': duration_ms,
            'timeout': timeout,
        }
        

    def reset_nodes(self):
        for node in self.nodes:
            node.message_log = []
            node.prepare_log = {}
            node.commit_log = {}
            node.current_phase = None