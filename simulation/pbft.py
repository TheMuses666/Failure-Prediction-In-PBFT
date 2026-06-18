class PBFT_protocol():
    def pre_prepare(self, primary, nodes, round_id):
        message = {
            'type': 'pre_prepare',
            'sender_id': primary.node_id,
            'round_id': round_id,
            'content': f'request_{round_id}'  
        }

        primary.broadcast(nodes, message)

    def prepare(self, primary, nodes, round_id):
        for node in nodes:
            if node.node_id != primary.node_id:
                prepare_message = {
                    'type': 'prepare',
                    'sender_id': node.node_id,
                    'round_id': round_id,
                    'content': f'request_{round_id}'  
                }
                node.broadcast(nodes, prepare_message)
        
    def commit(self, nodes, round_id):
        for node in nodes:
            commit_message = {
                'type': 'commit',
                'sender_id': node.node_id,
                'round_id': round_id,
                'content': f'request_{round_id}'  
            }
            node.broadcast(nodes, commit_message)

    def check_consensus(self, nodes, round_id, quorum):
        success_count = 0
        for node in nodes:
            commits = node.commit_log.get(round_id, [])
            if len(commits) >= quorum:
                success_count +=1

        return success_count
    
    def reply(self, nodes, round_id):
        replies = []
        for node in nodes:
            if round_id in node.commit_log:
                replies.append({
                    "type": "reply",
                    "sender_id": node.node_id,
                    "round_id": round_id,
                    "content": f"reply_{round_id}"
                })
        return replies