#!/bin/bash

# Script para limpeza dos recursos

echo "=== Limpeza CPU Stress Test ==="

echo "Removendo Deployment..."
microk8s kubectl delete deployment cpu-stress-test --ignore-not-found

echo "Removendo Service..."
microk8s kubectl delete service cpu-stress-service --ignore-not-found

echo "Removendo ConfigMap..."
microk8s kubectl delete configmap stress-config --ignore-not-found

echo "Removendo Jobs..."
microk8s kubectl delete job cpu-stress-job --ignore-not-found

echo "Removendo imagem..."
microk8s ctr image rm docker.io/library/cpu-stress:latest || true

echo "=== Limpeza concluída ==="