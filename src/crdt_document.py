"""
crdt_document.py - Documento simples com operações por posição
"""

class CRDTDocument:
    """Mantém o texto como string e aplica operações determinísticas"""

    def __init__(self):
        self.text = ""

    def _normalize_position(self, position: int) -> int:
        if position < 0:
            return 0
        if position > len(self.text):
            return len(self.text)
        return position

    def local_insert(self, position: int, text_value: str):
        """Insere texto localmente, substituindo chars do intervalo"""
        return self._apply_insert(position, text_value)

    def remote_insert(self, position: int, text_value: str):
        """Aplica inserção remota"""
        return self._apply_insert(position, text_value)

    def _apply_insert(self, position: int, text_value: str):
        if not text_value:
            return self._normalize_position(position), ""

        position = self._normalize_position(position)
        self.text = self.text[:position] + text_value + self.text[position:]
        return position, text_value

    def local_delete(self, position: int):
        """Remove caractere na posição, se existir"""
        return self._apply_delete(position)

    def remote_delete(self, position: int):
        """Aplica deleção remota"""
        return self._apply_delete(position)

    def _apply_delete(self, position: int):
        if not self.text:
            return None, position

        position = self._normalize_position(position)
        if position >= len(self.text):
            return None, position

        removed_char = self.text[position]
        self.text = self.text[:position] + self.text[position + 1:]
        return removed_char, position

    def get_text(self):
        return self.text

    def get_visible_length(self):
        return len(self.text)

    def __repr__(self):
        return f"Document: '{self.text}' ({len(self.text)} chars)"
