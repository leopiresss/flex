#!/bin/bash
echo "=== DIAGNÓSTICO DO GRAFANA ==="

echo "1. Status do MicroK8s:"
microk8s status

echo -e "\n2. API do Kubernetes:"
microk8s kubectl cluster-info

echo -e "\n3. Pods do Observability:"
microk8s kubectl get pods -n observability

echo -e "\n4. Pods com Problemas:"
microk8s kubectl get pods -n observability --field-selector=status.phase!=Running

echo -e "\n5. Eventos Recentes:"
microk8s kubectl get events -n observability --sort-by='.lastTimestamp' | tail -10

echo -e "\n6. Verificar Conectividade da API:"
if curl -k -s --connect-timeout 5 https://10.152.183.1:443/version > /dev/null; then
    echo "✅ API está respondendo"
else
    echo "❌ API não está respondendo"
fi

echo -e "\n7. ServiceAccount do Grafana:"
microk8s kubectl get sa -n observability | grep grafana

microk8s kubectl port-forward  --address 0.0.0.0 -n observability service/kube-prom-stack-grafana    9090:80 &