#!/bin/bash

echo "🔍 Diagnosticando falha do cAdvisor"

# Verificar status dos pods
echo "1. Status dos pods cAdvisor:"
microk8s kubectl get pods -n monitoring -l app=cadvisor -o wide

# Verificar eventos
echo -e "\n2. Eventos recentes:"
microk8s kubectl get events -n monitoring --sort-by='.lastTimestamp' | grep cadvisor | tail -10

# Verificar logs do pod
echo -e "\n3. Logs do container cAdvisor:"
POD_NAME=$(microk8s kubectl get pods -n monitoring -l app=cadvisor -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -n "$POD_NAME" ]; then
    echo "Pod: $POD_NAME"
    echo "Logs atuais:"
    microk8s kubectl logs -n monitoring "$POD_NAME" --tail=50
    
    echo -e "\nLogs anteriores (se disponível):"
    microk8s kubectl logs -n monitoring "$POD_NAME" --previous --tail=20 2>/dev/null || echo "Logs anteriores não disponíveis"
else
    echo "❌ Nenhum pod cAdvisor encontrado"
fi

# Verificar descrição do pod
echo -e "\n4. Descrição do pod:"
if [ -n "$POD_NAME" ]; then
    microk8s kubectl describe pod -n monitoring "$POD_NAME" | tail -30
fi

# Verificar recursos do sistema
echo -e "\n5. Recursos do sistema:"
echo "Nodes:"
microk8s kubectl get nodes -o wide

echo -e "\nRecursos disponíveis:"
microk8s kubectl top nodes 2>/dev/null || echo "Metrics server não disponível"

# Verificar volumes e permissões
echo -e "\n6. Verificando volumes críticos:"
echo "Containerd socket:"
ls -la /var/snap/microk8s/common/run/containerd.sock 2>/dev/null || echo "❌ Socket containerd não encontrado"

echo "cgroups:"
ls -la /sys/fs/cgroup/ | head -5

echo "Proc:"
ls -la /proc/ | head -3

echo -e "\n✅ Diagnóstico concluído!"