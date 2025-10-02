# Salvar a imagem em um arquivo tar
docker save memory-stress:latest > memory-stress.tar

# Importar para o MicroK8s
microk8s ctr image import memory-stress.tar

# Verificar se foi importada
microk8s ctr images ls | grep memory-stress

microk8s kubectl apply -f deployment.yaml

# Ver imagens no MicroK8s
#microk8s ctr images ls

# Ver status do pod
microk8s kubectl get pods
microk8s kubectl describe pod memory-stress