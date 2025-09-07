#!/bin/bash
#instalando port-forward do cAdvisor
source ~/flex/lib/port-lib.sh 


kubectl create namespace monitoring
kubectl apply  -f prometheus-config.yaml -n monitoring
kubectl apply -f prometheus-autenticacao.yaml -n monitoring
kubectl apply -f prometheus-deployment.yaml -n monitoring
kubectl apply -f prometheus-service.yaml -n monitoring

# Verificar pods
kubectl get pods -n monitoring

# Verificar serviços
kubectl get svc -n monitoring

microk8s kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=500s


# kubectl port-forward --address 0.0.0.0 svc/prometheus-service 9090:9090 -n monitoring &


echo "✅ Instalando conectividade"

# Parâmetros para chamar a função
RESOURCE_TYPE="svc"
RESOURCE_NAME="prometheus-service"
NAMESPACE="monitoring"
LOCAL_PORT="9090"
REMOTE_PORT="9090"
LOCAL_INTERFACE="0.0.0.0"
PID_FILE="/tmp/cadivisor-pf.pid"
NET_IFACE="ens33"
RESOURCE_NOME_SISTEMA="PROMETHEUS"



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





