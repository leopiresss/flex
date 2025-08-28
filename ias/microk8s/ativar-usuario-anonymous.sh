#!/bin/bash

echo "⚠️  ATENÇÃO: Isso vai habilitar acesso anônimo ao kubelet!"
echo "Isso é INSEGURO e deve ser usado apenas para desenvolvimento/teste."
read -p "Tem certeza que quer continuar? (yes/no): " confirm

if [[ $confirm != "yes" ]]; then
    echo "Operação cancelada."
    exit 1
fi

echo "🔧 Fazendo backup da configuração..."
sudo cp /var/snap/microk8s/current/args/kubelet /var/snap/microk8s/current/args/kubelet.backup

echo "📝 Modificando configuração do kubelet..."

# Remover configurações antigas se existirem
sudo sed -i '/--anonymous-auth/d' /var/snap/microk8s/current/args/kubelet
sudo sed -i '/--authorization-mode/d' /var/snap/microk8s/current/args/kubelet

# Adicionar novas configurações
echo "--anonymous-auth=true" | sudo tee -a /var/snap/microk8s/current/args/kubelet
echo "--authorization-mode=AlwaysAllow" | sudo tee -a /var/snap/microk8s/current/args/kubelet

echo "🔄 Reiniciando MicroK8s..."
microk8s stop
sleep 5
microk8s start
microk8s status --wait-ready

echo "✅ Testando acesso anônimo..."
sleep 10

# Testar healthz
if curl -k -s https://127.0.0.1:10250/healthz | grep -q "ok"; then
    echo "✅ Healthz OK"
else
    echo "❌ Healthz falhou"
fi

# Testar métricas
echo "📊 Testando métricas..."
curl -k -s https://127.0.0.1:10250/metrics/cadvisor | head -5

echo "⚠️  Lembre-se: Isso é inseguro! Reverta quando terminar os testes."