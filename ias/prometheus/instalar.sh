
kubectl create namespace monitoring
kubectl apply -f clusterRole.yml
kubectl apply -f config-map.yml
kubectl apply -f prometheus-deployment.yml
kubectl get deployments –n monitoring
kubectl apply -f prometheus-service.yml
microk8s kubectl port-forward --address 0.0.0.0 -n monitoring svc/kube-prom-stack-kube-prome-prometheus 9091:9090 &
