kubectl apply -f prometheus-config.yaml
kubectl rollout restart deployment prometheus -n monitoring
microk8s kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=500s
kubectl port-forward --address 0.0.0.0 svc/prometheus-service 9090:9090 -n monitoring &
