
kubectl create namespace monitoring
kubectl apply -f clusterRole.yaml
kubectl apply -f config-map.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl get deployments –n monitoring
kubectl apply -f prometheus-service.yaml
microk8s kubectl port-forward --address 0.0.0.0 -n monitoring svc/prometheus-service 9090:9090 &
