"""
crdt_document.py - Implementação do RGA (Replicated Growable Array)
"""
from character import Character

class CRDTDocument:
    def __init__(self):
        # A lista contém objetos Character.
        # Começamos vazios. O "início do texto" é virtualmente representado por None/Start.
        self.characters = [] 

    def local_insert(self, index, char_value, site_id, vector_clock):
        """
        Gera o ID único para o novo char e descobre quem é o 'vizinho da esquerda' (origin).
        Retorna os dados necessários para criar a mensagem de broadcast.
        """
        # 1. Criar o ID único do novo caractere
        # Nota: Convertemos o dict do relógio para tupla para ser imutável/hashable se necessário
        # Mas aqui, manteremos simples: (clock_dict, site_id)
        # O PDF sugere Position ID = (VectorClock, site_id)
        new_pos_id = (vector_clock.get_copy(), site_id)
        
        # 2. Descobrir o ID do vizinho à esquerda (Origin)
        # Se index for 0, o origin é None (Início do Documento)
        visible_chars = [c for c in self.characters if not c.deleted]
        
        origin_pos_id = None
        if index > 0 and index <= len(visible_chars):
            # O vizinho é o caractere visível no índice anterior
            origin_pos_id = visible_chars[index - 1].position_id
        
        # 3. Criar o objeto caractere
        new_char = Character(char_value, new_pos_id, deleted=False)
        
        # 4. Inserir localmente usando a lógica RGA
        self._rga_insert(new_char, origin_pos_id)
        
        return new_char, origin_pos_id

    def remote_insert(self, char_dict, origin_pos_id):
        """
        Reconstrói o caractere vindo da rede e o insere na posição correta
        relativa ao seu 'origin'.
        """
        new_char = Character.from_dict(char_dict)
        
        # Verifica se já temos este caractere (idempotência)
        for c in self.characters:
            if c.position_id == new_char.position_id:
                return # Já existe, ignora

        self._rga_insert(new_char, origin_pos_id)
        return new_char

    def _rga_insert(self, new_char, origin_pos_id):
        """
        LÓGICA CORE DO RGA:
        1. Encontra o índice do 'origin'.
        2. Varre para a direita pulando caracteres que foram inseridos
           concorrentemente mas têm prioridade (ID maior).
        """
        insert_index = 0
        
        # Passo 1: Encontrar onde começa o origin na lista real (incluindo deletados)
        if origin_pos_id is not None:
            found = False
            for i, c in enumerate(self.characters):
                if c.position_id == origin_pos_id:
                    insert_index = i + 1
                    found = True
                    break
            # Se recebemos um origin que não temos (falha causal grave), 
            # por segurança anexamos ao fim (ou trataríamos buffer de espera).
            if not found:
                insert_index = len(self.characters)

        # Passo 2: Tratar concorrência (Skipping)
        # Se outros nós inseriram coisas APÓS o mesmo origin, precisamos decidir a ordem.
        # Regra: Se o próximo caractere tem o mesmo origin (concorrente),
        # ordenamos decrescentemente pelo ID (ou site_id) para consistência.
        
        # Simplificação robusta: Avançamos enquanto o caractere atual tiver um ID Maior
        # que o nosso. Isso garante que [Y, X] fiquem sempre na mesma ordem em todos os nós.
        while insert_index < len(self.characters):
            next_char = self.characters[insert_index]
            
            # Comparamos os IDs. O __lt__ do Character resolve (Clock, SiteID).
            # Se o next_char for "maior" (mais recente/maior site_id), ele fica à esquerda.
            # Nós pulamos ele.
            if new_char < next_char: 
                insert_index += 1
            else:
                break
        
        self.characters.insert(insert_index, new_char)

    def local_delete(self, index):
        """Marca como deletado baseado no índice visual"""
        visible_chars = [c for c in self.characters if not c.deleted]
        
        if 0 <= index < len(visible_chars):
            target_char = visible_chars[index]
            target_char.deleted = True
            return target_char # Retorna objeto para pegar o ID e enviar rede
        return None

    def remote_delete(self, target_pos_id):
        """Busca o caractere pelo ID único e marca tombstone"""
        for c in self.characters:
            # Precisamos comparar tuplas ou strings de forma consistente
            # O target_pos_id vem do JSON (listas em vez de tuplas no clock),
            # então a comparação direta pode falhar se não normalizada.
            # Assume-se que a normalização ocorre na entrada da mensagem.
            if c.position_id == target_pos_id:
                c.deleted = True
                return c
        return None

    def get_text(self):
        return "".join([c.value for c in self.characters if not c.deleted])
