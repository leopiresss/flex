#!/bin/bash

echo "🔑 Recuperando token do dashboard..."

# Verificar se o ServiceAccount existe
if ! microk8s kubectl get serviceaccount dashboard-admin -n kube-system &>/dev/null; then
    echo "❌ ServiceAccount 'dashboard-admin' não existe!"
    echo "Execute primeiro: microk8s kubectl create serviceaccount dashboard-admin -n kube-system"
    exit 1
fi

# Tentar recuperar de Secret permanente primeiro
echo "🔍 Verificando se existe Secret permanente..."
if microk8s kubectl get secret dashboard-admin-token -n kube-system &>/dev/null; then
    echo "✅ Secret encontrado! Recuperando token..."
    TOKEN=$(microk8s kubectl get secret dashboard-admin-token -n kube-system -o jsonpath='{.data.token}' | base64 -d)
    
    if [ ! -z "$TOKEN" ]; then
        echo ""
        echo "🎯 TOKEN RECUPERADO:"
        echo "==================="
        echo "$TOKEN"
        echo "==================="
        exit 0
    fi
fi

# Se não existe Secret, gerar novo token temporário
echo "⚠️  Secret permanente não encontrado. Gerando novo token..."
TOKEN=$(microk8s kubectl create token dashboard-admin -n kube-system --duration=8760h)

if [ ! -z "$TOKEN" ]; then
    echo ""
    echo "🎯 NOVO TOKEN GERADO:"
    echo "===================="
    echo "$TOKEN"
    echo "===================="
    echo ""
    echo "💡 DICA: Para ter um token permanente, execute:"
    echo "   ./create-permanent-token.sh"
else
    echo "❌ Falha ao gerar token!"
    exit 1
fi