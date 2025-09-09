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

# Passo 3: Habilitar novamente
echo "🔄 Habilitando observability..."
microk8s enable observability

# Passo 4: Aguardar inicialização
echo "⏱️  Aguardando inicialização dos pods..."
sleep 60

# Passo 5: Verificar status
echo "📊 Verificando status..."
microk8s kubectl get pods -n observability

echo "✅ Reinstalação concluída!"
echo ""
echo "Para acessar o Prometheus, execute:"
echo "microk8s kubectl port-forward --address 0.0.0.0 -n observability svc/kube-prom-stack-kube-prome-prometheus 9091:9090"
echo "Depois acesse: http://localhost:9091"