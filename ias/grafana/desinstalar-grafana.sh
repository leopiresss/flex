#!/bin/bash


echo ">> Apagando ConfigMap com DataSource do Prometheus..."
kubectl delete configmap grafana-datasources -n monitoring  

echo ">> Apagando Grafana..."
kubectl delete deployment grafana -n monitoring

echo ">> Apagando Service do Grafana..."
kubectl delete service grafana -n monitoring

sudo kill -9 $(lsof -ti:3000) 2>/dev/null || true

