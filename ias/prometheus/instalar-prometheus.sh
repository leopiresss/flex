#!/bin/bash
#instalando port-forward do cAdvisor
source ~/flex/lib/port-lib.sh 

echo " ⚠️ -  Criando namespace monitoring..."
kubectl create namespace monitoring

echo " ⚠️ -  Aplicando configuração do Prometheus..."
kubectl apply  -f prometheus-config.yaml -n monitoring

echo " ⚠️ -  Aplicando autenticação do Prometheus..."
kubectl apply -f prometheus-autenticacao.yaml -n monitoring

echo " ⚠️ -  Aplicando deployment do Prometheus..."
kubectl apply -f prometheus-deployment.yaml -n monitoring

echo " ⚠️ -  Aplicando service do Prometheus..."
kubectl apply -f prometheus-service.yaml -n monitoring

echo " ⚠️ -  Aplicando StorageClass do Alertmanager..."
kubectl apply -f alertmanager-storageclass.yaml -n monitoring

echo " ⚠️ -  Aplicando PersistentVolume do Alertmanager..."
kubectl apply -f alertmanager-pv.yaml -n monitoring

echo " ⚠️ -  Aplicando StatefulSet do Alertmanager..."
kubectl apply -f alertmanager-statefulset.yaml -n monitoring

echo " ⚠️ -  Aplicando ConfigMap do Alertmanager..."
kubectl apply -f configmap-alertmanager.yaml -n monitoring

echo " ⚠️ -  Instalando configuração do RBAC State Metrics..."
kubectl apply -f ksm-rbac.yaml

echo " ⚠️ -  Instalando deployment do Kube Satate Metric..."
kubectl apply -f prometheus-kube-sate-metric-deployment.yaml

echo " ⚠️ -  Aguardando pods do Prometheus ficarem prontos..."
microk8s kubectl wait --for=condition=ready pod -l app=kube-sate-metric-deployment -n monitoring --timeout=500s


echo " ⚠️ -  Instalando deploymento do Kube Satate Metric Service..."
kubectl apply -f prometheus-kube-sate-metric-service.yaml


echo " ⚠️ -  Aplicando service do Prometheus (segunda vez)..."
kubectl apply -f prometheus-service.yaml -n monitoring

echo " ⚠️ -  Verificando pods no namespace monitoring..."
kubectl get pods -n monitoring

echo " ⚠️ -  Verificando serviços no namespace monitoring..."
kubectl get svc -n monitoring



echo " ⚠️ -  Aguardando pods do Prometheus ficarem prontos..."
microk8s kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=500s

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

echo " ⚠️ -  Executando port-forward para o Prometheus..."
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



# Parâmetros para chamar a função
RESOURCE_TYPE="svc"
RESOURCE_NAME="kube-state-metrics"
NAMESPACE="monitoring"
LOCAL_PORT="8080"
REMOTE_PORT="8080"
LOCAL_INTERFACE="0.0.0.0"
PID_FILE="/tmp/kube-state-metrics-pf.pid"
NET_IFACE="ens33"
RESOURCE_NOME_SISTEMA="KUBE-STATE-METRICS"

echo " ⚠️ -  Executando port-forward para o Kube-state-metrics..."
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