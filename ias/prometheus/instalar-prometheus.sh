
kubectl create namespace monitoring
kubectl apply  -f prometheus-config.yaml -n monitoring
kubectl apply -f prometheus-autenticacao.yaml -n monitoring
kubectl apply -f prometheus-deployment.yaml -n monitoring
kubectl apply -f prometheus-service.yaml -n monitoring

# Verificar pods
kubectl get pods -n monitoring

# Verificar serviços
kubectl get svc -n monitoring

microk8s kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=500s

kubectl port-forward --address 0.0.0.0 svc/prometheus-service 9090:9090 -n monitoring &



