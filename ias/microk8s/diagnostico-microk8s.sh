#!/bin/bash

echo "=== DIAGNÓSTICO COMPLETO DO MICROK8S ==="

echo "1. Sistema de Arquivos:"
mount | grep -E "on / |on /var "
df -h | head -5
df -i | head -5

echo -e "\n2. Espaço em Disco MicroK8s:"
du -sh /var/snap/microk8s/ 2>/dev/null || echo "Diretório não encontrado"

echo -e "\n3. Processos MicroK8s:"
ps aux | grep microk8s | grep -v grep

echo -e "\n4. Status dos Serviços:"
systemctl status snap.microk8s.daemon-kubelite --no-pager -l
systemctl status snap.microk8s.daemon-containerd --no-pager -l

echo -e "\n5. Logs Recentes do Sistema:"
dmesg | tail -10

echo -e "\n6. Status do MicroK8s:"
microk8s status

echo -e "\n7. Pods Problemáticos:"
microk8s kubectl get pods -A | grep -E "(Error|CrashLoopBackOff|ImagePullBackOff|ContainerCreating)"

echo -e "\n8. Eventos Recentes:"
microk8s kubectl get events -A --sort-by='.lastTimestamp' | tail -10