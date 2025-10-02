echo "ok"

# Opção A: Usar registry do MicroK8s (Recomendado)
microk8s enable registry

# Build da imagem
docker build -t memory-stress:latest .

# Push para registry local
docker push memory-stress:latest

# Verificar
microk8s ctr images ls | grep memory-stress

# Salvar a imagem em um arquivo tar
docker save memory-stress:latest > memory-stress.tar

# Importar para o MicroK8s
microk8s ctr image import memory-stress.tar