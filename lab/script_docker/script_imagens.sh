#!/bin/bash

# Lista de repositórios para remover
repositories=(
    "localhost:32000/memory-stress:latest"
    "localhost:5000/memory-stress:latest"
    "memory-stress:latest"
    "localhost:32000/prime-server:latest"
    "redis:latest"
    "hello-world:latest"
    "registry:2"
)

echo "Removendo imagens Docker por repositório..."

for repo in "${repositories[@]}"; do
    echo "Removendo imagem: $repo"
    docker rmi -f "$repo"
done

# Remove imagens <none> (dangling images)
echo "Removendo imagens dangling (<none>)..."
docker image prune -f

echo "Processo concluído!"