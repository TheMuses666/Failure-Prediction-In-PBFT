from simulation.node import Node, Byzantine_Node
from config import NUM_BYZANTINE_NODES, NUM_NODES, RANDOM_SEED
import random

class FaultInjector():
    def create_nodes(self, fault_type):
        random.seed(RANDOM_SEED)

        all_nodes = list(range(NUM_NODES))
        byzantine_ids = random.sample(all_nodes, NUM_BYZANTINE_NODES)

        nodes = []
        for node_id in all_nodes:
            if node_id in byzantine_ids:
                nodes.append(Byzantine_Node(node_id,fault_type))
            else:
                nodes.append(Node(node_id))
        
        return nodes