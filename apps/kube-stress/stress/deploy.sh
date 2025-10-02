# Aplicar os manifestos
microk8s kubectl apply -f stress-namespace.yaml
microk8s kubectl apply -f simple_stress_deployment.yaml

# Verificar criação do namespace
microk8s kubectl get namespaces

# Verificar deployments
microk8s kubectl get deployments -n stress-test

# Verificar pods
microk8s kubectl get pods -n stress-test

# Ver status detalhado
microk8s kubectl get pods -n stress-test -o wide