#!/bin/bash

echo "=== Diagnóstico cAdvisor MicroK8s ==="

# Verificar MicroK8s
echo "📍 Status MicroK8s:"
microk8s status --wait-ready

# Obter nome do nó
NODE_NAME=$(microk8s kubectl get nodes --no-headers | awk '{print $1}' | head -1)
echo "🎯 Nó: $NODE_NAME"

# Iniciar proxy
echo -e "\n🔧 Iniciando proxy..."
microk8s kubectl proxy --port=8081 &
PROXY_PID=$!
sleep 3

echo -e "\n📊 Testando endpoints disponíveis:"

# Testar diferentes endpoints
endpoints=(
    "/metrics/cadvisor"
    "/metrics"
    "/stats/summary"
    "/healthz"
    "/configz"
    "/logs"
)

for endpoint in "${endpoints[@]}"; do
    echo "Testando: $endpoint"
    response=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8081/api/v1/nodes/$NODE_NAME/proxy$endpoint")
    if [[ "$response" == "200" ]]; then
        echo "✅ $endpoint - OK"
        
        # Se for um endpoint de métricas, mostrar amostra
        if [[ "$endpoint" == *"metrics"* ]] || [[ "$endpoint" == *"stats"* ]]; then
            echo "📋 Amostra do conteúdo:"
            curl -s "http://localhost:8081/api/v1/nodes/$NODE_NAME/proxy$endpoint" | head -10
            echo "..."
        fi
    else
        echo "❌ $endpoint - HTTP $response"
    fi
    echo ""
done

# Verificar configuração do kubelet
echo "🔧 Configuração do kubelet:"
sudo cat /var/snap/microk8s/current/args/kubelet | grep -E "(cadvisor|metrics|port)"

# Verificar processos
echo -e "\n🔍 Processos relacionados:"
ps aux | grep -E "(cadvisor|kubelet)" | grep -v grep

# Verificar portas
echo -e "\n🌐 Portas em uso:"
sudo netstat -tlnp | grep -E "(10250|4194|8080|10255)"

# Limpar proxy
kill $PROXY_PID 2>/dev/null
echo -e "\n✅ Diagnóstico concluído!"