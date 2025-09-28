#!/bin/bash

# Script para build e deploy no microk8s

echo "=== CPU Stress Test - Build e Deploy ==="

# Verifica se microk8s está rodando
if ! microk8s status --wait-ready; then
    echo "Erro: microk8s não está rodando"
    exit 1
fi

# Build da imagem Docker
echo "Construindo imagem Docker..."
docker build -t prime-server:latest .

# Importa imagem para microk8s
echo "Importando imagem para microk8s..."
docker save prime-server:latest | microk8s ctr image import -

# Aplica manifests
#echo "Aplicando ConfigMap..."
#microk8s kubectl apply -f configmap.yaml

echo "Aplicando Service..."
microk8s kubectl apply -f service.yaml

echo "Aplicando Ingress..."
microk8s kubectl apply -f ingress.yaml


echo "Aplicando Deployment..."
microk8s kubectl apply -f deployment.yaml

echo "=== Deploy concluído ==="
echo "Para monitorar:"
echo "microk8s kubectl get pods -l app=prime-server"
echo "microk8s kubectl logs -f deployment/prime-server-test"
echo "microk8s kubectl top pods"

