#!/bin/bash

echo "🚀 Instalando cAdvisor no namespace monitoring para monitorar stress-app"

# Verificar se MicroK8s está rodando
if ! microk8s status --wait-ready; then
    echo "❌ MicroK8s não está rodando"
    exit 1
fi

# Criar namespaces
echo "📦 Criando namespaces..."
#microk8s kubectl create namespace monitoring --dry-run=client -o yaml | microk8s kubectl apply -f -
#microk8s kubectl create namespace stress-app --dry-run=client -o yaml | microk8s kubectl apply -f -

# Remover instalação anterior
echo "🧹 Removendo instalações anteriores..."
microk8s kubectl delete -f cadvisor-monitoring-namespace.yaml --ignore-not-found=true 2>/dev/null || true
microk8s kubectl delete daemonset cadvisor -n monitoring --ignore-not-found=true
sleep 5

# Aplicar nova configuração
echo "📄 Aplicando configuração no namespace monitoring..."
microk8s kubectl apply -f cadvisor-monitoring-namespace.yaml

# Aguardar deployment
echo "⏳ Aguardando pods ficarem prontos..."
microk8s kubectl rollout status daemonset/cadvisor -n monitoring --timeout=300s

# Verificar status
echo "✅ Status dos recursos no namespace monitoring:"
echo "Pods:"
microk8s kubectl get pods -n monitoring -l app=cadvisor -o wide

echo -e "\nServiços:"
microk8s kubectl get svc -n monitoring -l app=cadvisor

echo -e "\nServiceMonitor:"
microk8s kubectl get servicemonitor -n monitoring -l app=cadvisor 2>/dev/null || echo "ServiceMonitor não encontrado (Prometheus Operator pode não estar instalado)"

# Obter informações de acesso
NODE_IP=$(microk8s kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
NODEPORT=$(microk8s kubectl get svc cadvisor -n monitoring -o jsonpath='{.spec.ports[0].nodePort}')

echo -e "\n🌐 URLs de acesso:"
echo "Interface Web (hostNetwork): http://$NODE_IP:8080"
echo "Interface Web (NodePort): http://$NODE_IP:$NODEPORT"
echo "Métricas Prometheus: http://$NODE_IP:8080/metrics"

# Testar conectividade
echo -e "\n🧪 Testando conectividade..."
sleep 10

if curl -s --connect-timeout 5 "http://$NODE_IP:8080/healthz" > /dev/null; then
    echo "✅ cAdvisor acessível via hostNetwork"
    WORKING_URL="http://$NODE_IP:4194"
elif curl -s --connect-timeout 5 "http://$NODE_IP:$NODEPORT/healthz" > /dev/null; then
    echo "✅ cAdvisor acessível via NodePort"
    WORKING_URL="http://$NODE_IP:$NODEPORT"
else
    echo "❌ cAdvisor não está acessível"
    WORKING_URL=""
fi

if [ -n "$WORKING_URL" ]; then
    echo -e "\n📊 Verificando métricas..."
    
    # Verificar métricas gerais
    TOTAL_METRICS=$(curl -s "$WORKING_URL/metrics" | wc -l)
    echo "Total de métricas: $TOTAL_METRICS"
    
    # Verificar métricas de containers
    CONTAINER_METRICS=$(curl -s "$WORKING_URL/metrics" | grep "container_" | wc -l)
    echo "Métricas de containers: $CONTAINER_METRICS"
    
    # Verificar métricas do namespace stress-app especificamente
    STRESS_APP_METRICS=$(curl -s "$WORKING_URL/metrics" | grep 'namespace="stress-app"' | wc -l)
    echo "Métricas do namespace stress-app: $STRESS_APP_METRICS"
    
    if [ "$STRESS_APP_METRICS" -gt 0 ]; then
        echo "✅ Namespace stress-app sendo monitorado!"
        echo "Exemplos de métricas do stress-app:"
        curl -s "$WORKING_URL/metrics" | grep 'namespace="stress-app"' | head -3
    else
        echo "⚠️  Namespace stress-app ainda não tem pods ou aguardando detecção..."
        echo "💡 Crie alguns pods no namespace stress-app para ver as métricas"
    fi
fi

echo -e "\n🎉 Deploy concluído!"
echo "📍 cAdvisor rodando no namespace: monitoring"
echo "🎯 Monitorando namespace: stress-app"
echo "🔗 URL principal: ${WORKING_URL:-'Use port-forward se necessário'}"

# Sugestão para criar pods de teste
echo -e "\n💡 Para testar, crie pods no namespace stress-app:"
echo "microk8s kubectl run stress-test --image=nginx -n stress-app"
echo "microk8s kubectl create deployment stress-app --image=nginx --replicas=3 -n stress-app"