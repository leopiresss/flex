#!/bin/bash

# Configurações
RELEASE_NAME="prometheus"  # Ajuste conforme necessário
NAMESPACE="monitoring"     # Ajuste conforme necessário

echo "Desinstalando Prometheus Operator..."

# 1. Desinstalar via Helm
echo "1. Removendo release do Helm..."
helm uninstall $RELEASE_NAME -n $NAMESPACE

# 2. Apagar CRDs
echo "2. Removendo CRDs do Prometheus Operator..."
kubectl delete crd $(kubectl get crd | grep monitoring.coreos.com | awk '{print $1}') 2>/dev/null

# 3. Apagar PVCs
echo "3. Removendo PersistentVolumeClaims..."
kubectl delete pvc --all -n $NAMESPACE 2>/dev/null

# 4. Apagar namespace
#echo "4. Removendo namespace..."
#kubectl delete namespace $NAMESPACE 2>/dev/null

#echo "Desinstalação concluída!"