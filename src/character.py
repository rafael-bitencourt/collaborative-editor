class Character:
    def __init__(self, value, position_id, deleted=False):
        self.value = value
        # position_id deve ser normalizado para (tuple_of_tuples, site_id)
        # para garantir comparação estável
        self.position_id = self._normalize_id(position_id)
        self.deleted = deleted
    
    def _normalize_id(self, pid):
        if pid is None: return None
        clock, site = pid
        
        # Se for Dicionário (Injeção Local)
        if isinstance(clock, dict):
            # Transforma dict em tupla de tuplas ordenada
            clock = tuple(sorted(clock.items()))
            
        # Se for Lista (Vindo do JSON/Rede)
        elif isinstance(clock, list):
            # IMPORTANTE: O JSON traz listas de listas [[k,v], [k,v]].
            # Precisamos converter as listas internas [k,v] em tuplas (k,v)
            # antes de converter a lista externa em tupla.
            clock = tuple(sorted(tuple(item) for item in clock))
            
        return (clock, site)
    
    def __lt__(self, other):
        # Lógica Crítica: Comparação de IDs para desempate
        # Primeiro compara clocks, depois site_id
        return self.position_id < other.position_id
        
    def to_dict(self):
        return {
            'value': self.value,
            'vector_clock': self.position_id[0], # Já é tupla
            'site_id': self.position_id[1],
            'deleted': self.deleted
        }
    
    @staticmethod
    def from_dict(data):
        # Reconstrói ID
        raw_clock = data['vector_clock'] # Vem como lista do JSON
        site = data['site_id']
        return Character(data['value'], (raw_clock, site), data['deleted'])
