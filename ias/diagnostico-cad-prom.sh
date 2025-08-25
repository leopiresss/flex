#!/bin/bash

echo "🔍 DIAGNÓSTICO DA CONFIGURAÇÃO ATUAL"
echo "=================================="

echo -e "\n📋 1. Verificando ServiceMonitors existentes:"
microk8s kubectl get servicemonitor -A | grep -E "(kubelet|cadvisor|node)"

echo -e "\n📋 2. Verificando se cAdvisor está acessível:"
# Testar acesso direto ao cAdvisor via kubelet
NODE_NAME=$(microk8s kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
echo "Testando no nó: $NODE_NAME"

# Verificar se o proxy funciona
microk8s kubectl proxy --port=8001 &
PROXY_PID=$!
sleep 3

echo -e "\n📊 3. Testando endpoint do cAdvisor:"
curl -s -k "http://localhost:8001/api/v1/nodes/$NODE_NAME/proxy/metrics/cadvisor" | head -5
CADVISOR_STATUS=$?

echo -e "\n📊 4. Verificando targets do Prometheus:"
# Port-forward do Prometheus
microk8s kubectl port-forward -n observability svc/prometheus-operated 9090:9090 &
PROM_PID=$!
sleep 3

echo "Verificando targets ativos..."
curl -s "http://localhost:9090/api/v1/targets" | jq -r '.data.activeTargets[] | select(.labels.job | contains("kubelet") or contains("cadvisor")) | "\(.labels.job): \(.health)"'

# Cleanup
kill $PROXY_PID $PROM_PID 2>/dev/null

if [ $CADVISOR_STATUS -eq 0 ]; then
    echo -e "\n✅ cAdvisor está acessível!"
else
    echo -e "\n❌ cAdvisor não está acessível diretamente"
fi

echo -e "\n📋 5. Verificando métricas do cAdvisor no Prometheus:"
echo "Execute manualmente:"
echo "microk8s kubectl port-forward -n observability svc/prometheus-operated 9090:9090"
echo "Depois acesse: http://localhost:9090/graph"
echo "E teste a query: container_cpu_usage_seconds_total"