#!/bin/bash
# setup-monitoring.sh

set -e

echo "=== Configurando Helm + MicroK8s ==="

# 1. Configurar kubeconfig
mkdir -p ~/.kube
microk8s config > ~/.kube/config
export KUBECONFIG=~/.kube/config

# 2. Adicionar ao bashrc
if ! grep -q "KUBECONFIG" ~/.bashrc; then
    echo 'export KUBECONFIG=~/.kube/config' >> ~/.bashrc
fi

# 3. Habilitar addons necessários
microk8s enable dns
microk8s enable metrics-server
microk8s enable storage

# 4. Adicionar repositório Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 5. Criar namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# 6. Instalar kube-prometheus-stack
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin123

echo ""
echo "=== Instalação Concluída ==="
echo ""
echo "Aguarde os pods ficarem prontos..."
kubectl wait --for=condition=ready pod -l "release=kube-prometheus-stack" -n monitoring --timeout=300s

echo ""
echo "=== Como acessar ==="
echo ""
echo "Grafana:"
echo "  kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80"
echo "  URL: http://localhost:3000"
echo "  User: admin"
echo "  Pass: admin123"
echo ""
echo "Prometheus:"
echo "  kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090"
echo "  URL: http://localhost:9090"
echo ""