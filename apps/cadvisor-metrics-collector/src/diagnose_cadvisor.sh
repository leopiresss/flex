#!/bin/bash

echo "🔍 Diagnóstico do cAdvisor"
echo "========================="

NAMESPACE="monitoring"

# Verificar MicroK8s
echo "1. Verificando MicroK8s..."
if command -v microk8s &> /dev/null; then
    echo "  ✅ MicroK8s instalado"
    microk8s version
    
    if snap list microk8s &> /dev/null; then
        echo "  📦 Instalação via Snap detectada"
        echo "  Path containerd: /var/snap/microk8s/common/run/containerd.sock"
    else
        echo "  📦 Instalação não-snap detectada"
        echo "  Path containerd: /run/containerd/containerd.sock"
    fi
else
    echo "  ❌ MicroK8s não encontrado"
    exit 1
fi

# Verificar pods
echo ""
echo "2. Verificando pods do cAdvisor..."
if microk8s kubectl get pods -n $NAMESPACE -l app=cadvisor &> /dev/null; then
    microk8s kubectl get pods -n $NAMESPACE -l app=cadvisor -o wide
    
    # Verificar logs de pods com problema
    echo ""
    echo "3. Logs dos pods:"
    microk8s kubectl get pods -n $NAMESPACE -l app=cadvisor --no-headers | while read pod status rest; do
        echo "--- Pod: $pod (Status: $status) ---"
        if [ "$status" != "Running" ]; then
            microk8s kubectl logs $pod -n $NAMESPACE --tail=20 || true
            echo ""
            microk8s kubectl describe pod $pod -n $NAMESPACE | grep -A 10 "Events:" || true
        else
            echo "Pod rodando normalmente"
        fi
        echo ""
    done
else
    echo "  ❌ Nenhum pod do cAdvisor encontrado"
fi

# Verificar service
echo ""
echo "4. Verificando service..."
if microk8s kubectl get svc cadvisor -n $NAMESPACE &> /dev/null; then
    microk8s kubectl get svc cadvisor -n $NAMESPACE
    microk8s kubectl get endpoints cadvisor -n $NAMESPACE
else
    echo "  ❌ Service não encontrado"
fi

# Verificar RBAC
echo ""
echo "5. Verificando RBAC..."
if microk8s kubectl get serviceaccount cadvisor -n $NAMESPACE &> /dev/null; then
    echo "  ✅ ServiceAccount existe"
else
    echo "  ❌ ServiceAccount não existe"
fi

if microk8s kubectl get clusterrole cadvisor &> /dev/null; then
    echo "  ✅ ClusterRole existe"
else
    echo "  ❌ ClusterRole não existe"
fi

if microk8s kubectl get clusterrolebinding cadvisor &> /dev/null; then
    echo "  ✅ ClusterRoleBinding existe"
else
    echo "  ❌ ClusterRoleBinding não existe"
fi

# Verificar recursos do sistema
echo ""
echo "6. Verificando recursos do sistema..."
echo "Nodes:"
microk8s kubectl get nodes -o wide

echo ""
echo "Uso de recursos nos nodes:"
microk8s kubectl top nodes 2>/dev/null || echo "Metrics server não disponível"

# Verificar containerd
echo ""
echo "7. Verificando containerd..."
if [ -S "/var/snap/microk8s/common/run/containerd.sock" ]; then
    echo "  ✅ Containerd socket (snap): /var/snap/microk8s/common/run/containerd.sock"
elif [ -S "/run/containerd/containerd.sock" ]; then
    echo "  ✅ Containerd socket (padrão): /run/containerd/containerd.sock"
else
    echo "  ❌ Socket do containerd não encontrado"
fi

echo ""
echo "========================="
echo "Diagnóstico concluído!"
echo "========================="