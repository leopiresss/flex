#!/bin/bash
#instalando port-forward do cAdvisor
source ~/flex/lib/port-lib.sh 


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




echo "✅ Instalado conectividade do cAdvisor"
# Parâmetros para chamar a função
RESOURCE_TYPE="svc"
RESOURCE_NAME="cadvisor-service"
NAMESPACE="monitoring"
LOCAL_PORT="8080"
REMOTE_PORT="8080"
LOCAL_INTERFACE="0.0.0.0"
PID_FILE="/tmp/cadivisor-pf.pid"
NET_IFACE="ens33"
RESOURCE_NOME_SISTEMA="CADVISOR"


# Chama a função principal da biblioteca, passando os argumentos necessários
executar_port_forward \
    "$RESOURCE_TYPE" \
    "$RESOURCE_NAME" \
    "$NAMESPACE" \
    "$LOCAL_PORT" \
    "$REMOTE_PORT" \
    "$LOCAL_INTERFACE" \
    "$PID_FILE" \
    "$NET_IFACE" \
    "$RESOURCE_NOME_SISTEMA"




