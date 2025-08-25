#!/bin/bash

echo "🔍 Diagnóstico Completo - cAdvisor sem Pods"
echo "============================================="

# 1. Verificar MicroK8s
echo "📦 Status do MicroK8s:"
microk8s status

# 2. Verificar nodes
echo -e "\n🖥️  Nodes disponíveis:"
kubectl get nodes -o wide

# 3. Verificar pods em execução
echo -e "\n🚀 Pods em execução:"
kubectl get pods -A --field-selector status.phase=Running | head -10

# 4. Verificar configuração do kubelet
echo -e "\n⚙️  Configuração do kubelet:"
sudo cat /var/snap/microk8s/current/args/kubelet | grep -E "(cadvisor|metrics|disable)" || echo "Nenhuma configuração específica encontrada"

# 5. Verificar containers no runtime
echo -e "\n📦 Containers no runtime:"
sudo /snap/microk8s/current/bin/crictl ps | head -5

# 6. Testar conectividade com cAdvisor
echo -e "\n🔗 Testando conectividade cAdvisor:"
if ! pgrep -f "kubectl proxy" > /dev/null; then
    kubectl proxy --port=8080 &
    sleep 3
fi

NODE_NAME=$(kubectl get nodes --no-headers -o custom-columns=":metadata.name" | head -1)
echo "Testando node: $NODE_NAME"

# Testar se retorna algo
CADVISOR_RESPONSE=$(curl -s "http://localhost:8080/api/v1/nodes/$NODE_NAME/proxy/metrics/cadvisor" | head -1)
if [ -n "$CADVISOR_RESPONSE" ]; then
    echo "✅ cAdvisor respondendo"
    
    # Verificar se há métricas de containers
    CONTAINER_METRICS=$(curl -s "http://localhost:8080/api/v1/nodes/$NODE_NAME/proxy/metrics/cadvisor" | grep "container_" | wc -l)
    echo "📊 Métricas de container encontradas: $CONTAINER_METRICS"
    
    # Verificar se há métricas de pods
    POD_METRICS=$(curl -s "http://localhost:8080/api/v1/nodes/$NODE_NAME/proxy/metrics/cadvisor" | grep 'pod=' | wc -l)
    echo "🎯 Métricas de pod encontradas: $POD_METRICS"
    
    if [ "$POD_METRICS" -eq 0 ]; then
        echo "⚠️  PROBLEMA: Nenhuma métrica de pod encontrada"
        
        # Mostrar algumas métricas disponíveis
        echo "📋 Primeiras métricas disponíveis:"
        curl -s "http://localhost:8080/api/v1/nodes/$NODE_NAME/proxy/metrics/cadvisor" | head -10
    fi
else
    echo "❌ cAdvisor não está respondendo"
fi

# 7. Verificar logs do kubelet
echo -e "\n📋 Logs recentes do kubelet (últimas 20 linhas):"
sudo journalctl -u snap.microk8s.daemon-kubelet -n 20 --no-pager | grep -E "(cadvisor|metrics|error)" || echo "Nenhum log relevante encontrado"

# 8. Verificar portas
echo -e "\n🔌 Portas do kubelet:"
sudo netstat -tlnp | grep kubelet || echo "Kubelet não encontrado nas portas"

echo -e "\n✅ Diagnóstico concluído!"