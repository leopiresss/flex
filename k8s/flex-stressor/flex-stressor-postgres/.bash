#!/bin/bash
# deploy.sh

echo "🐍 Fazendo deploy do ambiente de stress Python com PostgreSQL"

# Build da imagem
echo "📦 Construindo imagem Python..."
docker build -t stress-postgres-python:latest .

# Deploy do PostgreSQL
echo "🗄️ Fazendo deploy do PostgreSQL..."
kubectl apply -f postgres-deployment.yaml

# Aguardar PostgreSQL
echo "⏳ Aguardando PostgreSQL estar pronto..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Testar conexão
echo "🔍 Testando conexão com PostgreSQL..."
kubectl exec deployment/postgres -- pg_isready -U postgres

# Deploy da aplicação
echo "🔥 Fazendo deploy da aplicação Python..."
kubectl apply -f stress-deployment.yaml

# Deploy do HPA
echo "📊 Configurando HPA..."
kubectl apply -f hpa.yaml

echo "✅ Deploy concluído!"
echo ""
echo "📋 Comandos úteis:"
echo "   kubectl get pods -w"
echo "   kubectl get hpa -w"
echo "   kubectl logs -f deployment/stress-postgres-python"
echo "   kubectl exec -it deployment/postgres -- psql -U postgres -d stressdb"
echo ""
echo "🔍 Para monitorar:"
echo "   ./monitor.sh"