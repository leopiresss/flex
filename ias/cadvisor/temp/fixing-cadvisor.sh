#!/bin/bash

echo "=== RESET COMPLETO DO MICROK8S ==="

# 1. Parar tudo
echo "Parando MicroK8s..."
microk8s stop
sleep 10

# 2. Matar processos restantes
echo "Finalizando processos restantes..."
sudo pkill -f microk8s
sudo pkill -f containerd
sleep 5

# 3. Limpar diretórios problemáticos
echo "Limpando diretórios temporários..."
sudo rm -rf /var/snap/microk8s/common/run/containerd/
sudo rm -rf /tmp/microk8s-*
sudo rm -rf /var/snap/microk8s/common/var/lib/kubelet/pods/

# 4. Verificar e corrigir sistema de arquivos
echo "Verificando sistema de arquivos..."
if mount | grep -q "ro,"; then
    echo "Sistema em read-only, remontando..."
    sudo mount -o remount,rw /
fi

# 5. Recriar diretórios necessários
echo "Recriando estrutura de diretórios..."
sudo mkdir -p /var/snap/microk8s/common/run/containerd/
sudo mkdir -p /var/snap/microk8s/common/var/lib/kubelet/
sudo chown -R root:microk8s /var/snap/microk8s/common/
sudo chmod -R 755 /var/snap/microk8s/common/

# 6. Reiniciar serviços do snap
echo "Reiniciando serviços..."
sudo systemctl daemon-reload
sudo systemctl restart snapd
sleep 10

# 7. Iniciar MicroK8s
echo "Iniciando MicroK8s..."
microk8s start
microk8s status --wait-ready

echo "Reset concluído!"