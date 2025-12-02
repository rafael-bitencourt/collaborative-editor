#!/bin/bash

# ==============================================================================
# SCRIPT DE TESTE AVANÇADO - INE 5418
# Cobre: Inserção, Deleção, Concorrência no Meio, Idempotência e Caos
# ==============================================================================

# 1. Limpeza
echo "--- [SETUP] Limpando processos e pipes antigos ---"
pkill -f "python main.py"
rm -f pipe1 pipe2 pipe3

# 2. Criar Pipes
mkfifo pipe1 pipe2 pipe3

echo "--- [SETUP] Iniciando Nós (Leitores) em Background ---"
python3 -u main.py node1 <pipe1 >node1.log 2>&1 &
PID1=$!
python3 -u main.py node2 <pipe2 >node2.log 2>&1 &
PID2=$!
python3 -u main.py node3 <pipe3 >node3.log 2>&1 &
PID3=$!

echo "--- [SETUP] Aguardando 5s para handshake e conexões ---"
sleep 5

# 3. Abrir canais de escrita
exec 3>pipe1
exec 4>pipe2
exec 5>pipe3

# Função para ver o estado atual
show_state() {
    echo ""
    echo ">>> ESTADO ATUAL <<<"
    echo "Node 1: $(grep "Texto atual:" node1.log | tail -n 1)"
    echo "Node 2: $(grep "Texto atual:" node2.log | tail -n 1)"
    echo "Node 3: $(grep "Texto atual:" node3.log | tail -n 1)"
    echo "--------------------"
}

# ==============================================================================
# CENÁRIO 1: Inserção Concorrente (Básico)
# Estado Esperado: XY ou YX
# ==============================================================================
echo "--- CENÁRIO 1: Inserção Concorrente (X e Y na pos 0) ---"
echo "insert 0 X" >&3
echo "insert 0 Y" >&4

sleep 5
echo "show" >&3
echo "show" >&4
echo "show" >&5
sleep 1
show_state

# ==============================================================================
# PREPARAÇÃO PARA CENÁRIO 2
# Estado Esperado: XYM (ou YXM)
# ==============================================================================
echo "--- PREPARAÇÃO: Inserindo 'M' no final via Node 3 ---"
# Assumindo tamanho 2, insere na pos 2
echo "insert 2 M" >&5
echo "   ...Aguardando propagação (5s)..."
sleep 5
show_state

# ==============================================================================
# CENÁRIO 2: Inserção vs Deleção
# Estado Esperado: XYZ (M deletado, Z inserido)
# ==============================================================================
echo "--- CENÁRIO 2: Inserção de 'Z' (pos 3) e Deleção de 'M' (pos 2) ---"
# Z entra após o M (índice 3), M (índice 2) é deletado
echo "insert 3 Z" >&3
echo "delete 2" >&4

sleep 5
echo "show" >&3
echo "show" >&4
echo "show" >&5
sleep 1
show_state

# ==============================================================================
# CENÁRIO 3: O "Sanduíche" (Inserção Concorrente no Meio)
# Estado Atual Esperado: XYZ (Indices: 0, 1, 2)
# Ação: Node 1 insere 'A' na pos 1 (entre X e Y)
#       Node 3 insere 'B' na pos 1 (entre X e Y)
# Estado Final Esperado: XABYZ ou XBAYZ
# ==============================================================================
echo "--- CENÁRIO 3: Inserção Concorrente no Meio (Sanduíche) ---"
echo "   Inserindo 'A' e 'B' na posição 1 (entre o 1º e 2º caractere)..."

echo "insert 1 A" >&3
echo "insert 1 B" >&5

sleep 5
echo "show" >&3
echo "show" >&4
echo "show" >&5
sleep 1
show_state

# ==============================================================================
# CENÁRIO 4: Deleção Idempotente (Double Delete)
# Objetivo: Dois nós deletam o MESMO caractere simultaneamente.
# Ação: Vamos deletar o último caractere ('Z').
#       O tamanho atual deve ser 5 (ex: XABYZ). O último índice é 4.
# ==============================================================================
echo "--- CENÁRIO 4: Deleção Idempotente (Node 1 e 2 deletam o último char) ---"
echo "   Tentando deletar o caractere do índice 4 simultaneamente..."

echo "delete 4" >&3
echo "delete 4" >&4

sleep 5
echo "show" >&3
echo "show" >&4
echo "show" >&5
sleep 1
show_state

# ==============================================================================
# CENÁRIO 5: Caos (Conflito de 3 vias)
# Ação: Todos os 3 nós inserem no INÍCIO (pos 0) ao mesmo tempo.
# Caracteres: @, #, &
# ==============================================================================
echo "--- CENÁRIO 5: CAOS (3 nós inserem no início ao mesmo tempo) ---"
echo "   Node 1: @, Node 2: #, Node 3: &"

echo "insert 0 @" >&3
echo "insert 0 #" >&4
echo "insert 0 &" >&5

sleep 5
echo "show" >&3
echo "show" >&4
echo "show" >&5
sleep 1
show_state

# ==============================================================================
# ENCERRAMENTO
# ==============================================================================
echo "--- Encerrando ---"
exec 3>&-
exec 4>&-
exec 5>&-
sleep 1
pkill -f "python main.py"
rm pipe1 pipe2 pipe3
echo "Testes concluídos."
