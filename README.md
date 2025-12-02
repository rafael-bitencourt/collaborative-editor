# Editor de Texto Colaborativo com CRDT

Trabalho 2 - INE5418 Computação Distribuída
Sistema de edição colaborativa com consistência eventual usando CRDTs.

## 📁 Estrutura de Diretórios

```
collaborative-editor/
├── src/
│   ├── character.py        # Classe Character (elemento do CRDT)
│   ├── vector_clock.py     # Implementação de relógio vetorial
│   ├── crdt_document.py    # CRDT de Sequência (RGA)
│   ├── node.py             # Nó distribuído principal
│   ├── run_test.sh         # Testes automatizados
│   └── main.py             # Interface CLI
└── README.txt
```

## 🚀 Como Executar

### Requisitos
- Python 3.8+
- Nenhuma biblioteca externa necessária (usa apenas biblioteca padrão)

### Passos para Execução

## Execução Manual (Nó a Nó)

1. **Abra 3 terminais diferentes**

2. **Terminal 1 - Node 1:**
```bash
cd src
python3 main.py node1
```

3. **Terminal 2 - Node 2:**
```bash
cd src
python3 main.py node2
```

4. **Terminal 3 - Node 3:**
```bash
cd src
python3 main.py node3
```

## Execução automatizada (script bash)

1. **Dê permissão de execução ao script:**
```bash
cd src
chmod +x run_test.sh
```

2. **Execute  o script:**
```bash
./run_test.sh
```


## 📝 Comandos Disponíveis

- `insert <pos> <char>` - Insere caractere na posição especificada
- `delete <pos>` - Deleta caractere na posição especificada
- `show` - Mostra documento e estado do relógio vetorial
- `log` - Mostra últimas 10 operações
- `help` - Mostra ajuda
- `quit` - Sai do programa

## 🏗️ Arquitetura

### Classes Principais

- **Character**: Representa um caractere atômico contendo seu valor, um identificador único imutável (`position_id`) e uma flag de estado (`deleted`). Implementa a lógica de comparação (`__lt__`) para ordenação determinística.
- **VectorClock**: Gerencia os relógios lógicos para rastreamento causal de eventos entre os nós.
- **CRDTDocument**: Implementa a lógica do **RGA (Replicated Growable Array)**. Mantém a lista linear de caracteres e gerencia inserções relativas (baseadas em um caractere de origem) e deleções lógicas (tombstones).
- **Node**: Gerencia a camada de rede (Sockets TCP), o *broadcast* de mensagens, a serialização/desserialização de dados e a sincronização de threads.

### Protocolo de Mensagens

As mensagens são trocadas em formato JSON. Foi implementada uma **serialização customizada** para garantir que Tuplas (usadas nos IDs locais) sejam convertidas corretamente para Listas (JSON) e reconstruídas como Tuplas no destino, evitando erros de tipagem na comparação.

**Inserção:**
```json
{
  "type": "insert",
  "op_id": {"node1": 5, "node2": 3, "node3": 1},
  "site_id": "node1",
  "char": {
    "value": "A",
    "vector_clock": [["node1", 5], ["node2", 3]], 
    "site_id": "node1", 
    "deleted": false
  },
  "origin_id": [["node1", 4], ["node2", 3], "node1"] // ID do vizinho à esquerda
}
```

**Deleção:**
```json
{
  "type": "delete",
  "site_id": "node2",
  "target_id": [["node1", 5], ["node2", 3], "node1"] // ID exato do caractere a remover
}
```

## 🔧 Detalhes de Implementação

- **Algoritmo CRDT**: RGA (Replicated Growable Array). Garante que inserções concorrentes na mesma posição sejam ordenadas de forma consistente em todos os nós (desempate via site_id em caso de relógios idênticos).

- **Endereçamento**: Inserções são relativas ao origin_id (caractere anterior), garantindo que o texto não se "misture" incorretamente mesmo se a lista remota tiver tamanho diferente.

- **Tombstones**: Deleções são lógicas. O caractere é marcado como deleted=True, mas permanece na estrutura para garantir a integridade de referências futuras (causalidade).

- **Consistência**: Strong Eventual Consistency (SEC) atingida. Todos os nós convergem para o mesmo estado visual e interno após a troca de mensagens.

- **Tratamento de Tipos**: Normalização robusta na entrada de dados (_deserialize_id) para converter listas JSON em tuplas Python hashable.

## 📊 Limitações Conhecidas

- **Acúmulo de Lixo (Memory Leak)**: Caracteres deletados (tombstones) nunca são removidos da memória. Em um ambiente de produção, seria necessário um Garbage Collection distribuído.

- **Escalabilidade de Rede**: Topologia Full-mesh com configuração estática (hardcoded para 3 nós em localhost). Não possui peer discovery dinâmico.

- **Recuperação de Falhas**: Não há persistência em disco ou mecanismo de reconexão automática se um nó cair e voltar (o nó reiniciado perderia o histórico).
