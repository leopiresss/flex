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

#Instalar node-exporter
#  helm install node-exporter prometheus-community/prometheus-node-exporter

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
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80 &

#Cria um note port
kubectl get svc -n monitoring kube-prometheus-stack-grafana

kubectl patch svc kube-prometheus-stack-grafana -n monitoring --type='json' -p='[
  {"op": "replace", "path": "/spec/type", "value": "NodePort"},
  {"op": "add", "path": "/spec/ports/0/nodePort", "value": 30000}
]'
# 1. Verificar o service após a mudança para NodePort
kubectl get svc -n monitoring kube-prometheus-stack-grafana
# 2. Verificar a porta NodePort alocada
kubectl get svc -n monitoring kube-prometheus-stack-grafana -o yaml | grep -A 5 ports

# 3. Verificar se o pod está respondendo
kubectl get pods -n monitoring | grep grafana 


kubectl get svc -n monitoring kube-prometheus-stack-grafana -o yaml | grep -A 5 ports


echo ""
echo "Prometheus:"
echo "  kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090"
echo "  URL: http://localhost:9090"
echo ""
#kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090 &
#Cria um note port
kubectl get svc -n monitoring kube-prometheus-stack-prometheus
kubectl patch svc kube-prometheus-stack-prometheus -n monitoring -p '{"spec": {"type": "NodePort", "ports": [{"port": 9090, "targetPort": 9090, "nodePort": 30090, "name": "http-web"}]}}'
# 1. Verificar o service após a mudança para NodePort
kubectl get svc -n monitoring kube-prometheus-stack-prometheus
# 2. Verificar a porta NodePort alocada
kubectl get svc -n monitoring kube-prometheus-stack-prometheus -o yaml | grep -A 5 ports

# 3. Verificar se o pod está respondendo
kubectl get pods -n monitoring | grep prometheus 


kubectl get svc -n monitoring kube-prometheus-stack-prometheus -o yaml | grep -A 5 ports