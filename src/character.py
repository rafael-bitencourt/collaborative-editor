"""
character.py - Representa um caractere no CRDT
"""

class Character:
    """
    Representa um caractere no documento distribuído.
    Cada caractere tem um ID único para ordenação e um flag de deleção.
    """
    
    def __init__(self, value, position_id, deleted=False):
        """
        Args:
            value (str): O caractere em si
            position_id (tuple): (vector_clock_dict, site_id) para ordenação única
            deleted (bool): Flag indicando se o caractere foi removido
        """
        self.value = value
        self.position_id = position_id  # (vector_clock, site_id)
        self.deleted = deleted
    
    def __lt__(self, other):
        """Comparação para ordenação de caracteres baseada no Position ID"""
        return self.position_id < other.position_id
    
    def __eq__(self, other):
        """Igualdade baseada no Position ID"""
        return self.position_id == other.position_id
    
    def to_dict(self):
        """Serializa para envio via rede"""
        vector_clock, site_id = self.position_id
        serialized_clock = [(node, ts) for node, ts in vector_clock]
        return {
            'value': self.value,
            'vector_clock': serialized_clock,
            'site_id': site_id,
            'deleted': self.deleted
        }
    
    @staticmethod
    def from_dict(data):
        """Deserializa de mensagem recebida"""
        raw_clock = data['vector_clock']

        if isinstance(raw_clock, dict):
            normalized_clock = tuple(sorted(raw_clock.items()))
        else:
            normalized_clock = tuple((node, ts) for node, ts in raw_clock)

        site_id = data['site_id']
        position_id = (normalized_clock, site_id)
        return Character(data['value'], position_id, data['deleted'])
    
    def __repr__(self):
        return f"Char('{self.value}', id={self.position_id[1]}, del={self.deleted})"
