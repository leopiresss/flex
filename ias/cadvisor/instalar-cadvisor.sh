# 1. Criar namespace
microk8s kubectl apply -f cadvisor-namespace.yaml

# 2. Aplicar RBAC
microk8s kubectl apply -f cadvisor-rbac.yaml

# 3. Criar DaemonSet
microk8s kubectl apply -f cadvisor-daemonset.yaml

# 4. Criar Service
microk8s kubectl apply -f cadvisor-service.yaml


