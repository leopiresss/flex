kubectl delete configmap  prometheus-config -n monitoring
kubectl delete deployment prometheus -n monitoring
kubectl delete clusterrolebinding prometheus 
kubectl delete clusterrole prometheus
kubectl delete service prometheus-service
sudo kill -9 $(lsof -ti:9090) 2>/dev/null || true