#!/bin/bash

echo "🧼 Iniciando a desinstalação do MicroK8s..."

# Para o MicroK8s
echo "⛔ Parando o MicroK8s..."
sudo microk8s stop

# Remove o MicroK8s via snap
echo "🗑️ Removendo o pacote snap do MicroK8s..."
sudo snap remove microk8s

# Remove o grupo microk8s
echo "👥 Removendo grupo microk8s (se existir)..."
sudo groupdel microk8s 2>/dev/null

# Remove o usuário do grupo microk8s (caso ainda esteja)
echo "👤 Removendo o usuário atual do grupo microk8s..."
sudo gpasswd -d $USER microk8s 2>/dev/null

# Remove diretórios residuais
echo "🧹 Limpando arquivos residuais..."
sudo rm -rf ~/.kube
sudo rm -rf /var/snap/microk8s
sudo rm -rf /var/snap/microk8s/common
sudo rm -rf /var/snap/microk8s/current

# Remove alias do kubectl (se tiver sido criado)
echo "🔧 Removendo alias do kubectl..."
sudo snap unalias kubectl 2>/dev/null

echo "✅ MicroK8s completamente desinstalado!"
