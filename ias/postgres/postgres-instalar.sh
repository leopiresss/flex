# Recriar tudo
kubectl apply -f postgres-configmap.yaml
kubectl apply -f postgres-pv-pvc.yaml
kubectl apply -f postgres-deployment.yaml  # (versão com ConfigMap)
kubectl apply -f postgres-service.yaml