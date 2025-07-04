#!/bin/bash

# Script para deploy do PostgreSQL no Kubernetes com verificações completas

set -e  # Parar em caso de erro

echo "🔍 Verificando configuração do kubectl..."

# Verificar se kubectl está instalado
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl não está instalado"
    exit 1
fi

# Verificar se consegue conectar ao cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Não foi possível conectar ao cluster Kubernetes"
    exit 1
fi

echo "✅ kubectl configurado corretamente"

# Verificar se os arquivos YAML existem
for file in postgres-configmap.yaml postgres-pv-pvc.yaml postgres-deployment.yaml postgres-service.yaml; do
    if [ ! -f "$file" ]; then
        echo "❌ Arquivo $file não encontrado"
        exit 1
    fi
done

echo "🚀 Iniciando deploy do PostgreSQL..."

# 1. Aplicar os manifestos
echo "📋 Aplicando manifestos..."
kubectl apply -f postgres-configmap.yaml
kubectl apply -f postgres-pv-pvc.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f postgres-service.yaml

echo "⏳ Aguardando deployment ser criado..."
sleep 5

# Verificar se o deployment foi criado
if kubectl get deployment postgres-deployment &> /dev/null; then
    echo "✅ Deployment criado com sucesso"
    
    # Aguardar pods ficarem prontos
    echo "⏳ Aguardando pods ficarem prontos..."
    kubectl wait --for=condition=available deployment/postgres-deployment --timeout=300s
    
    # 2. Verificar o status
    echo "📊 Verificando status..."
    kubectl get pods -l app=postgres
    kubectl get services -l app=postgres
    kubectl get pvc
    
    # 3. Verificar logs apenas se o deployment existir
    echo "📝 Verificando logs..."
    kubectl logs deployment/postgres-deployment --tail=20
    
    echo "✅ Deploy concluído!"
    echo "🔗 Para conectar ao PostgreSQL:"
    echo "kubectl exec -it deployment/postgres-deployment -- psql -U postgres -d mydb"
else
    echo "❌ Deployment não foi criado. Verificando erros..."
    kubectl get events --sort-by=.metadata.creationTimestamp | tail -10
fi