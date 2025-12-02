"""
vector_clock.py - Implementação de Relógio Vetorial
"""

class VectorClock:
    """
    Relógio vetorial para rastreamento causal de eventos.
    Mantém um contador para cada nó no sistema.
    """
    
    def __init__(self, node_id, known_nodes):
        """
        Args:
            node_id (str): ID do nó local
            known_nodes (list): Lista de IDs de todos os nós conhecidos
        """
        self.node_id = node_id
        self.clock = {node: 0 for node in known_nodes}
    
    def increment(self):
        """Incrementa o contador do nó local antes de uma operação"""
        self.clock[self.node_id] += 1
    
    def update(self, received_clock):
        """
        Atualiza o relógio ao receber uma mensagem.
        Pega o máximo entre o clock local e o recebido para cada entrada.
        
        Args:
            received_clock (dict): Relógio vetorial recebido
        """
        for node_id, timestamp in received_clock.items():
            if node_id in self.clock:
                self.clock[node_id] = max(self.clock[node_id], timestamp)
            else:
                self.clock[node_id] = timestamp
    
    def get_copy(self):
        """Retorna uma cópia do relógio atual"""
        return self.clock.copy()
    
    def __repr__(self):
        return f"VectorClock({self.clock})"
