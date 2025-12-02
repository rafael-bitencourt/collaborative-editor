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
│   └── main.py             # Interface CLI
├── tests/
│   └── test_scenarios.py   # Cenários de teste
├── README.md
└── requirements.txt
```

## 🚀 Como Executar

### Requisitos
- Python 3.8+
- Nenhuma biblioteca externa necessária (usa apenas biblioteca padrão)

### Passos para Execução

1. **Abra 3 terminais diferentes**

2. **Terminal 1 - Node 1:**
```bash
cd src
python main.py node1
```

3. **Terminal 2 - Node 2:**
```bash
cd src
python main.py node2
```

4. **Terminal 3 - Node 3:**
```bash
cd src
python main.py node3
```

## 📝 Comandos Disponíveis

- `insert <pos> <char>` - Insere caractere na posição especificada
- `delete <pos>` - Deleta caractere na posição especificada
- `show` - Mostra documento e estado do relógio vetorial
- `log` - Mostra últimas 10 operações
- `help` - Mostra ajuda
- `quit` - Sai do programa

## 🧪 Cenários de Teste

### Teste 1: Inserção Concorrente
1. Em node1: `insert 0 X`
2. Em node2: `insert 0 Y` (ao mesmo tempo)
3. Verificar: ambos convergem para mesma ordem (XY ou YX)

### Teste 2: Inserção e Deleção Concorrente
1. Em node1: `insert 0 A`
2. Em node1: `insert 1 B`
3. Em node2: `delete 0` (deleta A)
4. Em node1: `insert 1 C` (insere C entre A e B)
5. Verificar: todos convergem para mesmo estado

## 🏗️ Arquitetura

### Classes Principais

- **Character**: Representa um caractere com ID único e flag de deleção
- **VectorClock**: Rastreamento causal de eventos
- **CRDTDocument**: Gerencia lista ordenada de caracteres (RGA)
- **Node**: Coordena comunicação TCP e operações CRDT

### Protocolo de Mensagens

Formato JSON:
```json
{
  "type": "insert"|"delete",
  "op_id": {"node1": 5, "node2": 3, "node3": 1},
  "site_id": "node1",
  "char_data": {...} ou "pos_id": [...]
}
```

## 🔧 Detalhes de Implementação

- **Ordenação**: Position ID = (VectorClock, site_id)
- **Comunicação**: TCP full-mesh (cada nó conecta com todos)
- **Consistência**: Strong Eventual Consistency (SEC)
- **Idempotência**: Verificação de duplicatas antes de inserir

## 📊 Limitações Conhecidas

- Hardcoded para 3 nós em localhost
- Sem persistência de dados
- Sem reconexão automática em caso de falha
- UI CLI simples (não é editor visual completo)
