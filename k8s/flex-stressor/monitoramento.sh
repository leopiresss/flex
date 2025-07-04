# Monitorar recursos dos pods
kubectl top pods --all-namespaces

# Monitorar eventos de escalonamento
kubectl get events --sort-by=.metadata.creationTimestamp

# Verificar status do HPA
kubectl get hpa -w

# Logs detalhados
kubectl logs -f deployment/stress-test