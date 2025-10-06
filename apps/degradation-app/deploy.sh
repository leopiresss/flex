# Deploy da aplicação principal
kubectl apply -f deployment.yaml

# Verificar se está rodando
kubectl get pods -n tcc-degradacao

# Ver logs
kubectl logs -f -n tcc-degradacao deployment/app-degradacao