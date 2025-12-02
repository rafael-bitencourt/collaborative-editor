#!/bin/bash

# ==============================================================================
# CORREÇÃO: Ordem de inicialização invertida para evitar Deadlock nos Pipes
# ==============================================================================

# 1. Limpeza
echo "--- Limpando processos e pipes antigos ---"
pkill -f "python main.py"
rm -f pipe1 pipe2 pipe3

# 2. Criar Pipes
mkfifo pipe1 pipe2 pipe3

echo "--- Iniciando Nós (Leitores) em Background ---"
# IMPORTANTE: Iniciamos o Python PRIMEIRO. Ele vai tentar ler o pipe e ficará
# esperando (bloqueado em background) até nós abrirmos o pipe para escrita.
# Isso evita que o script shell trave.

python3 -u main.py node1 <pipe1 >node1.log 2>&1 &
PID1=$!
python3 -u main.py node2 <pipe2 >node2.log 2>&1 &
PID2=$!
python3 -u main.py node3 <pipe3 >node3.log 2>&1 &
PID3=$!

echo "Nós iniciados (PIDs: $PID1, $PID2, $PID3). Abrindo canais de comunicação..."

# Pequena pausa para garantir que os processos Python já estão 'ouvindo' os pipes
sleep 1

# 3. Agora é seguro abrir os pipes para escrita (File Descriptors 3, 4, 5)
# O comando não vai travar porque os leitores (Python) já existem.
exec 3>pipe1
exec 4>pipe2
exec 5>pipe3

echo "Canais abertos. Aguardando convergência de rede (5s)..."
sleep 5

# Função para ver o estado atual
show_state() {
    echo ""
    echo ">>> ESTADO ATUAL <<<"
    # Pega a última linha que contém "Texto atual"
    echo "Node 1: $(grep "Texto atual:" node1.log | tail -n 1)"
    echo "Node 2: $(grep "Texto atual:" node2.log | tail -n 1)"
    echo "Node 3: $(grep "Texto atual:" node3.log | tail -n 1)"
    echo "===================="
}

# ==============================================================================
# CENÁRIO 1: Inserção Concorrente
# "Node ID1 insere 'X' e Node ID2 insere 'Y' na mesma posição"
# ==============================================================================
echo "--- CENÁRIO 1: Inserção Concorrente (X e Y na pos 0) ---"

echo "insert 0 X" >&3
echo "insert 0 Y" >&4

sleep 2
# Força atualização da tela
echo "show" >&3
echo "show" >&4
echo "show" >&5
sleep 1
show_state

# ==============================================================================
# PREPARAÇÃO CENÁRIO 2
# ==============================================================================
echo "--- Preparando (Inserindo 'M' no final via Node 3) ---"
# O texto deve estar com tamanho 2 (ex: "XY" ou "YX"). Inserimos na pos 2.
echo "insert 2 M" >&5
sleep 2
show_state

# ==============================================================================
# CENÁRIO 2: Inserção/Deleção Concorrente
# "Node ID1 insere 'Z'. Concorrentemente, Node ID2 deleta o caractere anterior"
# ==============================================================================
echo "--- CENÁRIO 2: Inserção de 'Z' (pos 3) e Deleção de 'M' (pos 2) ---"

echo "insert 3 Z" >&3
echo "delete 2" >&4

sleep 2
echo "show" >&3
echo "show" >&4
echo "show" >&5
sleep 1
show_state

# ==============================================================================
# ENCERRAMENTO
# ==============================================================================
echo "--- Encerrando ---"
# Fecha os descritores, o que envia EOF para os nós
exec 3>&-
exec 4>&-
exec 5>&-

sleep 1
pkill -f "python main.py"
rm pipe1 pipe2 pipe3
echo "Teste finalizado. Verifique node1.log, node2.log e node3.log para detalhes."
