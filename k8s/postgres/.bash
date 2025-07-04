# 1. Aplicar os manifestos
kubectl apply -f postgres-configmap.yaml
kubectl apply -f postgres-pv-pvc.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f postgres-service.yaml

# 2. Verificar o status
kubectl get pods
kubectl get services
kubectl get pvc

# 3. Verificar logs
kubectl logs -f deployment/postgres-deployment

# 4. Conectar ao PostgreSQL (para teste)
kubectl exec -it deployment/postgres-deployment -- psql -U postgres -d mydb