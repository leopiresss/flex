#!/bin/bash

# Carrega a biblioteca com as funções e variáveis
source ~/flex/lib/port-lib.sh  # ou . ./port-lib.sh

# Parâmetros para chamar a função
RESOURCE_TYPE="service"
RESOURCE_NAME="kubernetes-dashboard"
NAMESPACE="kube-system"
LOCAL_PORT="10443"
REMOTE_PORT="443"
LOCAL_INTERFACE="0.0.0.0"
PID_FILE="/tmp/microk8s-dashboard-pf.pid"
NET_IFACE="ens33"

print_status "Iniciando port-forward para $RESOURCE_TYPE/$RESOURCE_NAME ($NAMESPACE:$REMOTE_PORT -> $LOCAL_INTERFACE:$LOCAL_PORT)..."


# Chama a função principal da biblioteca, passando os argumentos necessários
executar_port_forward \
    "$RESOURCE_TYPE" \
    "$RESOURCE_NAME" \
    "$NAMESPACE" \
    "$LOCAL_PORT" \
    "$REMOTE_PORT" \
    "$LOCAL_INTERFACE" \
    "$PID_FILE" \
    "$NET_IFACE"

 usage