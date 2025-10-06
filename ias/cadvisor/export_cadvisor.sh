#!/bin/bash
#instalando port-forward do cAdvisor

echo "✅ Instalado conectividade do cAdvisor"
# Parâmetros para chamar a função
RESOURCE_TYPE="svc"
RESOURCE_NAME="cadvisor"
NAMESPACE="monitoring"
LOCAL_PORT="8070"
REMOTE_PORT="8070"
LOCAL_INTERFACE="127.0.0.1"
PID_FILE="/tmp/cadivisor-pf.pid"
NET_IFACE="ens33"
RESOURCE_NOME_SISTEMA="CADVISOR"

echo "Iniciando port-forward para $RESOURCE_TYPE/$RESOURCE_NAME ($NAMESPACE:$REMOTE_PORT -> $LOCAL_INTERFACE:$LOCAL_PORT)..."
microk8s kubectl port-forward --address 127.0.0.1 -n monitoring svc/cadvisor 8070:8070 &
