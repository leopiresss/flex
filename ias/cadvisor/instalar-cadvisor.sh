echo "Iniciando a instalação do cAdvisor..."
echo ""

# 1. Criar namespace
microk8s kubectl apply -f cadvisor-namespace.yaml

# 2. Aplicar RBAC
microk8s kubectl apply -f cadvisor-rbac.yaml

# 3. Criar DaemonSet
microk8s kubectl apply -f cadvisor-daemonset.yaml

# 4. Criar Service
microk8s kubectl apply -f cadvisor-service.yaml

microk8s kubectl port-forward  --address 0.0.0.0 -n monitoring svc/cadvisor 8080:8080 &

