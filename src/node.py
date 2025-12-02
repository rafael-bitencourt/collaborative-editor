"""
node.py - Nó do editor colaborativo distribuído
"""
import socket
import threading
import json
from vector_clock import VectorClock
from crdt_document import CRDTDocument

class Node:
    """
    Representa um nó no sistema distribuído.
    Gerencia conexões TCP, operações CRDT e consistência eventual.
    """
    
    def __init__(self, node_id, host, port, peers):
        """
        Args:
            node_id (str): ID único do nó
            host (str): IP para escutar
            port (int): Porta para escutar
            peers (list): Lista de (node_id, host, port) dos outros nós
        """
        self.node_id = node_id
        self.host = host
        self.port = port
        self.peers = peers
        
        # Inicializa relógio vetorial com todos os nós conhecidos
        all_nodes = [node_id] + [p[0] for p in peers]
        self.vector_clock = VectorClock(node_id, all_nodes)
        
        # Documento CRDT
        self.document = CRDTDocument()
        
        # Conexões TCP
        self.connections = {}  # {node_id: socket}
        self.server_socket = None
        self.running = False
        
        # Log de operações
        self.operation_log = []
        
        # Lock para sincronização
        self.lock = threading.Lock()
    
    def start(self):
        """Inicia o nó: servidor TCP e conexões com peers"""
        self.running = True
        
        # Inicia servidor TCP
        server_thread = threading.Thread(target=self._start_server, daemon=True)
        server_thread.start()
        
        # Aguarda um pouco antes de conectar aos peers
        threading.Timer(2.0, self._connect_to_peers).start()
    
    def _start_server(self):
        """Thread que escuta por conexões de outros nós"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"[Node {self.node_id}] Servidor escutando em {self.host}:{self.port}")
        
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                self._send_handshake(conn)
                thread = threading.Thread(target=self._handle_connection, args=(conn, None), daemon=True)
                thread.start()
            except:
                break
    
    def _connect_to_peers(self):
        """Conecta-se a todos os peers conhecidos"""
        for peer_id, peer_host, peer_port in self.peers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((peer_host, peer_port))
                
                with self.lock:
                    self.connections[peer_id] = sock
                
                print(f"[Node {self.node_id}] Conectado ao peer {peer_id}")
                
                self._send_handshake(sock)

                # Thread para receber mensagens deste peer
                thread = threading.Thread(target=self._handle_connection, args=(sock, peer_id), daemon=True)
                thread.start()
            except Exception as e:
                print(f"[Node {self.node_id}] Erro ao conectar com {peer_id}: {e}")
    
    def _handle_connection(self, conn, peer_id=None):
        """Thread que recebe mensagens de uma conexão"""
        buffer = ""
        remote_id = peer_id
        while self.running:
            try:
                data = conn.recv(4096).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        try:
                            msg = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        if msg.get('type') == 'hello':
                            remote_id = msg.get('node_id')
                            if remote_id:
                                self._register_connection(remote_id, conn)
                            continue

                        self._process_message(msg)
            except Exception as e:
                print(f"[Node {self.node_id}] Erro na conexão: {e}")
                break
        
        conn.close()
        if remote_id:
            with self.lock:
                if self.connections.get(remote_id) is conn:
                    del self.connections[remote_id]

    def _register_connection(self, peer_id, conn):
        """Garante que o socket esteja registrado para broadcasts"""
        with self.lock:
            self.connections[peer_id] = conn

    def _send_handshake(self, conn):
        """Envia mensagem de identificação do nó"""
        try:
            handshake = json.dumps({'type': 'hello', 'node_id': self.node_id}) + '\n'
            conn.sendall(handshake.encode('utf-8'))
        except Exception as e:
            print(f"[Node {self.node_id}] Erro enviando handshake: {e}")
    
    def _process_message(self, msg):
        """Processa uma mensagem recebida"""
        try:
            with self.lock:
                # Atualiza relógio vetorial
                self.vector_clock.update(msg['op_id'])
                
                # Aplica operação
                if msg['type'] == 'insert':
                    applied_pos, applied_text = self.document.remote_insert(
                        msg['position'], msg['text']
                    )
                    self.operation_log.append(
                        f"Remote INSERT: '{applied_text}' at pos {applied_pos} from {msg['site_id']}"
                    )
                
                elif msg['type'] == 'delete':
                    removed_char, applied_pos = self.document.remote_delete(msg['position'])
                    char_snippet = f" '{removed_char}'" if removed_char is not None else ""
                    self.operation_log.append(
                        f"Remote DELETE{char_snippet} at pos {applied_pos} from {msg['site_id']}"
                    )
        
        except Exception as e:
            print(f"[Node {self.node_id}] Erro processando mensagem: {e}")
    
    def insert(self, position, text_value):
        """Insere texto localmente e propaga"""
        if not text_value:
            return
        with self.lock:
            self.vector_clock.increment()
            applied_pos, applied_text = self.document.local_insert(position, text_value)
            self.operation_log.append(
                f"Local INSERT: '{applied_text}' at pos {applied_pos}"
            )
            message = {
                'type': 'insert',
                'op_id': self.vector_clock.get_copy(),
                'site_id': self.node_id,
                'position': applied_pos,
                'text': applied_text
            }
            self._broadcast(message)
    
    def delete(self, position):
        """
        Deleta um caractere localmente e propaga para peers.
        
        Args:
            position (int): Posição visual a deletar
        """
        with self.lock:
            # Incrementa relógio vetorial
            self.vector_clock.increment()
            
            # Deleta localmente
            removed_char, applied_pos = self.document.local_delete(position)
            
            if removed_char is not None:
                self.operation_log.append(
                    f"Local DELETE '{removed_char}' at pos {applied_pos}"
                )
                message = {
                    'type': 'delete',
                    'op_id': self.vector_clock.get_copy(),
                    'site_id': self.node_id,
                    'position': applied_pos
                }
                self._broadcast(message)
    
    def _broadcast(self, message):
        """Envia mensagem para todos os peers conectados"""
        msg_str = json.dumps(message) + '\n'
        
        for peer_id, conn in list(self.connections.items()):
            try:
                conn.sendall(msg_str.encode('utf-8'))
            except Exception as e:
                print(f"[Node {self.node_id}] Erro enviando para {peer_id}: {e}")
    
    def get_text(self):
        """Retorna texto atual do documento"""
        with self.lock:
            return self.document.get_text()
    
    def get_log(self, last_n=10):
        """Retorna últimas N operações do log"""
        with self.lock:
            return self.operation_log[-last_n:]
    
    def stop(self):
        """Para o nó e fecha conexões"""
        self.running = False
        
        for conn in self.connections.values():
            try:
                conn.close()
            except:
                pass
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
