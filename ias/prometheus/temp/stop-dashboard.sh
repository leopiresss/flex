#!/bin/bash

echo "🛑 Parando dashboard do MicroK8s..."

# Parar port-forward
if [ -f /tmp/microk8s-dashboard-pf.pid ]; then
    PID=$(cat /tmp/microk8s-dashboard-pf.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Port-forward parado (PID: $PID)"
    else
        echo "⚠️  Port-forward já estava parado"
    fi
    rm -f /tmp/microk8s-dashboard-pf.pid
else
    echo "⚠️  Arquivo PID não encontrado"
fi

# Matar qualquer processo na porta 10443
if lsof -ti:10443 &> /dev/null; then
    sudo kill -9 $(lsof -ti:10443) 2>/dev/null
    echo "✅ Processos na porta 10443 finalizados"
fi

echo "🎯 Dashboard parado com sucesso!"
