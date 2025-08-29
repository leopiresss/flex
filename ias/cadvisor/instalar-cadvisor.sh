#!/bin/bash

echo "🚀 Instalando cAdvisor v1.3 no MicroK8s"

# Verificar se MicroK8s está rodando
if ! microk8s status --wait-ready; then
    echo "❌ MicroK8s não está rodando"
    exit 1
fi

# Aplicar configurações
echo "📄 Aplicando ConfigMap..."
microk8s kubectl apply -f cadvisor-configmap.yaml

echo "📄 Aplicando RBAC..."
microk8s kubectl apply -f cadvisor-rbac.yaml

echo "📄 Aplicando DaemonSet..."
microk8s kubectl apply -f cadvisor-daemonset.yaml

echo "📄 Aplicando Service..."
microk8s kubectl apply -f cadvisor-service.yaml

# Aguardar pods ficarem prontos
echo "⏳ Aguardando pods ficarem prontos..."
microk8s kubectl rollout status daemonset/cadvisor -n monitoring --timeout=300s

# Verificar status
echo "✅ Status dos pods cAdvisor:"
microk8s kubectl get pods -n monitoring -l app=cadvisor -o wide


# Testar conectividade
echo "🔧 Testando conectividade..."
NODE_IP=$(microk8s kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

echo "Testando API v1.3..."
curl -s "http://$NODE_IP:8080/api/v1.3/version" || echo "❌ Falha na conectividade"

echo "📊 Testando métricas de containers..."
curl -s "http://$NODE_IP:8080/api/v1.3/containers" | head -10 || echo "❌ Falha ao obter containers"

echo "🎉 Instalação concluída!"
echo "Acesse: http://$NODE_IP:8080 para interface web"
echo "API v1.3: http://$NODE_IP:8080/api/v1.3/"