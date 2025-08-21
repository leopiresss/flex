
kubectl create namespace monitoring
kubectl apply -f clusterRole.yml
kubectl apply -f config-map.yml
kubectl apply -f prometheus-deployment.yml
kubectl get deployments –n monitoring
kubectl apply -f prometheus-service.yml
