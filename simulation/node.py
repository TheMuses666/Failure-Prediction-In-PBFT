import time
from config import BYZANTINE_DELAY_MS
class Node():
    def __init__(self, node_id, is_Byzantine=False):
        self.node_id = node_id
        self.is_Byzantine = is_Byzantine

        self.role = 'replica'
        self.current_phase = None
        self.message_log = []
        self.alive = True
        self.view_number = 0
        self.prepare_log = {}
        self.commit_log = {}
        # Request phase
        self.round_id = 0
        self.current_request = None

        # Counts
        self.timeout_count = 0 # Timeout_frequency
        self.vote_history = []  # voting_consistency


    def receive_message(self,message):
        if not self.alive:
            return
        
        self.message_log.append(message)

        msg_type = message['type']
        msg_sender = message['sender_id']
        msg_round = message['round_id']
        self.current_phase = msg_type

        if msg_type == 'prepare':
            if msg_round not in self.prepare_log:
                self.prepare_log[msg_round] = []
                self.prepare_log[msg_round].append(msg_sender)

        if msg_type == 'commit':
            if msg_round not in self.commit_log:
                self.commit_log[msg_round] = []
                self.commit_log[msg_round].append(msg_sender)


    def send_message(self, target_node, message):
        if not self.alive:
            return

        target_node.receive_message(message)


    def broadcast(self, all_nodes, message):
        for node in all_nodes:
            if self.node_id != node.node_id:
                self.send_message(node,message)


class Byzantine_Node(Node):
    def __init__(self, node_id, fault_type):
        super().__init__(node_id, is_Byzantine=True)
        self.fault_type = fault_type

    def send_message(self, target_node, message):
        if not self.alive:
            return
        
        if self.fault_type == 'silent':
            return
        
        elif self.fault_type == 'replay':
            if self.message_log:
                target_node.receive_message(self.message_log[0])
            else:
                target_node.receive_message(message)

        elif self.fault_type == 'equivocation':
            fake_message = message.copy()
            fake_message['content'] = 'fake_content'
            target_node.receive_message(fake_message)

        elif self.fault_type == 'delay':

            time.sleep(BYZANTINE_DELAY_MS / 1000)
            target_node.receive_message(message)

