"""
main.py - Interface CLI para o editor colaborativo
"""
import sys
import time
from node import Node

def print_help():
    """Imprime comandos disponíveis"""
    print("\n=== Comandos Disponíveis ===")
    print("  insert <pos> <texto> - Insere texto na posição (substitui o trecho atual)")
    print("  delete <pos>         - Deleta caractere na posição")
    print("  show                 - Mostra documento atual")
    print("  log                  - Mostra últimas 10 operações")
    print("  help                 - Mostra esta ajuda")
    print("  quit                 - Sai do programa")
    print("============================\n")

def main():
    """Função principal do programa"""
    
    if len(sys.argv) != 2:
        print("Uso: python main.py <node_id>")
        print("Node IDs disponíveis: node1, node2, node3")
        sys.exit(1)
    
    node_id = sys.argv[1]
    
    # Configuração dos nós (hardcoded para 3 nós)
    nodes_config = {
        'node1': ('localhost', 5001, [('node2', 'localhost', 5002), ('node3', 'localhost', 5003)]),
        'node2': ('localhost', 5002, [('node1', 'localhost', 5001), ('node3', 'localhost', 5003)]),
        'node3': ('localhost', 5003, [('node1', 'localhost', 5001), ('node2', 'localhost', 5002)])
    }
    
    if node_id not in nodes_config:
        print(f"Erro: Node ID '{node_id}' inválido")
        print("Node IDs disponíveis: node1, node2, node3")
        sys.exit(1)
    
    # Cria e inicia o nó
    host, port, peers = nodes_config[node_id]
    node = Node(node_id, host, port, peers)
    
    print(f"\n{'='*50}")
    print(f"  Editor Colaborativo - Nó {node_id}")
    print(f"{'='*50}")
    
    node.start()
    
    # Aguarda conexões serem estabelecidas
    print("\nAguardando conexões com peers...")
    time.sleep(3)
    
    print_help()
    
    # Loop de comandos
    try:
        while True:
            try:
                # Mostra texto atual e prompt
                text = node.get_text()
                print(f"\nTexto atual: [{text}]")
                print(f"Posições:     ", end="")
                for i in range(len(text)):
                    print(f"{i}", end="")
                print()
                
                command = input(f"\n[{node_id}]> ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd == 'insert':
                    if len(parts) < 3:
                        print("Erro: use 'insert <pos> <texto>'")
                        continue
                    
                    try:
                        pos = int(parts[1])
                        text_value = ' '.join(parts[2:])
                        if not text_value:
                            print("Erro: texto vazio não é permitido")
                            continue
                        node.insert(pos, text_value)
                        print(f"✓ Inserido '{text_value}' a partir da posição {pos}")
                    except (ValueError, IndexError):
                        print("Erro: posição inválida ou texto faltando")
                
                elif cmd == 'delete':
                    if len(parts) != 2:
                        print("Erro: use 'delete <pos>'")
                        continue
                    
                    try:
                        pos = int(parts[1])
                        node.delete(pos)
                        print(f"✓ Deletado caractere na posição {pos}")
                    except ValueError:
                        print("Erro: posição inválida")
                
                elif cmd == 'show':
                    print(f"\nDocumento completo: '{node.get_text()}'")
                    print(f"Relógio vetorial: {node.vector_clock}")
                
                elif cmd == 'log':
                    print("\n--- Últimas 10 operações ---")
                    for op in node.get_log(10):
                        print(f"  {op}")
                    print("----------------------------")
                
                elif cmd == 'help':
                    print_help()
                
                elif cmd == 'quit' or cmd == 'exit':
                    print("\nEncerrando...")
                    break
                
                else:
                    print(f"Comando desconhecido: '{cmd}'. Digite 'help' para ajuda.")
            
            except KeyboardInterrupt:
                print("\n\nEncerrando...")
                break
            except Exception as e:
                print(f"Erro: {e}")
    
    finally:
        node.stop()
        print("Nó encerrado.")

if __name__ == '__main__':
    main()
