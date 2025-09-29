
# disponibilizar o app de exemplo do chaos-mesh
kubectl port-forward deployment/web-show 8081:8081 --address 0.0.0.0

# apagar o networkchaos.yaml
kubectl delete -f networkchaos.yaml