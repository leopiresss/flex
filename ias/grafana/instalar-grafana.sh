#!/bin/bash

echo ">> Criando namespace monitoring..."
kubectl apply -f grafana-namespace.yaml

echo ">> Aplicando ConfigMap com DataSource do Prometheus..."
kubectl apply -f grafana-configmap.yaml

echo ">> Implantando Grafana..."
kubectl apply -f grafana-deployment.yaml

echo ">> Criando Service do Grafana..."
kubectl apply -f grafana-service.yaml

echo ">> Aguardando pods ficarem prontos..."
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=60s

if [ $? -eq 0 ]; then
    echo "Grafana instalado com sucesso!"
else
    echo "Timeout aguardando pods do dashboard"
    exit 1
fi

echo ">> Acesse via: http://<node-ip>:3000"
echo ">> Login: admin / Senha: admin123"
kubectl port-forward --address 0.0.0.0 svc/grafana 3000:3000 -n monitoring &