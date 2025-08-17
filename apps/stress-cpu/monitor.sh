#!/bin/bash

# Script para monitoramento do stress test

echo "=== Monitoramento CPU Stress Test ==="

# Função para mostrar status
show_status() {
    echo "--- Pods ---"
    microk8s kubectl get pods -l app=cpu-stress
    
    echo ""
    echo "--- Recursos ---"
    microk8s kubectl top pods -l app=cpu-stress
    
    echo ""
    echo "--- Logs (últimas 10 linhas) ---"
    microk8s kubectl logs -l app=cpu-stress --tail=10
}

# Monitoramento contínuo
if [ "$1" = "--watch" ]; then
    while true; do
        clear
        show_status
        echo ""
        echo "Pressione Ctrl+C para parar o monitoramento"
        sleep 5
    done
else
    show_status
fi