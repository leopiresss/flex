#!/bin/bash

echo "🗑️  Iniciando reinstalação limpa do observability..."

# Passo 1: Desabilitar
echo "Desabilitando observability..."
microk8s disable observability

# Passo 2: Aguardar limpeza
echo "Aguardando limpeza (30 segundos)..."
sleep 30

# Verificar se foi limpo
echo "Verificando limpeza..."
if microk8s kubectl get namespaces | grep -q observability; then
    echo "⚠️  Namespace ainda existe, aguardando mais..."
    sleep 15
fi

# Verificar porta
if ss -tlpn | grep -q :9090; then
    echo "⚠️  Porta 9090 ainda em uso, liberando..."
    sudo fuser -k 9090/tcp 2>/dev/null
fi