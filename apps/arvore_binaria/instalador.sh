#!/bin/bash

# Script de Quick Start para MicroK8s
# Execute: bash quickstart-microk8s.sh

set -e

echo "=========================================="
echo "Memory Stress Test - MicroK8s Setup"
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se MicroK8s está instalado
if ! command -v microk8s &> /dev/null; then
    echo -e "${RED}❌ MicroK8s não encontrado!${NC}"
    echo "Instale com: sudo snap install microk8s --classic"
    exit 1
fi

echo -e "${GREEN}✓ MicroK8s encontrado${NC}"

# Verificar se MicroK8s está rodando
if ! microk8s status --wait-ready > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ MicroK8s não está rodando. Iniciando...${NC}"
    microk8s start
    microk8s status --wait-ready
fi

echo -e "${GREEN}✓ MicroK8s está rodando${NC}"

# Habilitar addons necessários
echo ""
echo "Habilitando addons necessários..."

ADDONS=("dns" "metrics-server")
for addon in "${ADDONS[@]}"; do
    if microk8s status | grep -q "$addon: enabled"; then
        echo -e "${GREEN}✓ $addon já está habilitado${NC}"
    else
        echo -e "${YELLOW}⚙ Habilitando $addon...${NC}"
        microk8s enable $addon
    fi
done

# Perguntar sobre registry local
echo ""
read -p "Deseja usar o registry local do MicroK8s? (s/n): " use_registry

if [[ $use_registry == "s" || $use_registry == "S" ]]; then
    if microk8s status | grep -q "registry: enabled"; then
        echo -e "${GREEN}✓ Registry já está habilitado${NC}"
    else
        echo -e "${YELLOW}⚙ Habilitando registry...${NC}"
        microk8s enable registry
    fi
    
    REGISTRY="localhost:32000"
    IMAGE_NAME="$REGISTRY/memory-stress:latest"
    
    echo ""
    echo -e "${YELLOW}Building e fazendo push da imagem...${NC}"
    docker build -t $IMAGE_NAME .
    docker push $IMAGE_NAME
    
    echo -e "${GREEN}✓ Imagem enviada para registry local${NC}"
else
    IMAGE_NAME="memory-stress:latest"
    
    echo ""
    echo -e "${YELLOW}Building da imagem...${NC}"
    docker build -t $IMAGE_NAME .
    
    echo -e "${YELLOW}Salvando imagem...${NC}"
    docker save $IMAGE_NAME > memory-stress.tar
    
    echo -e "${YELLOW}Importando imagem para MicroK8s...${NC}"
    microk8s ctr image import memory-stress.tar
    
    echo -e "${GREEN}✓ Imagem importada com sucesso${NC}"
    
    # Limpar arquivo temporário
    rm memory-stress.tar
fi

# Aguardar metrics-server estar pronto
echo ""
echo -e "${YELLOW}⏳ Aguardando metrics-server estar pronto...${NC}"
sleep 10

# Criar/atualizar deployment com a imagem correta
echo ""
echo -e "${YELLOW}Aplicando manifesto Kubernetes...${NC}"

# Atualizar imagem no deployment
sed "s|image: memory-stress:latest|image: $IMAGE_NAME|g" deployment.yaml > deployment-temp.yaml

microk8s kubectl apply -f deployment-temp.yaml

rm deployment-temp.yaml

# Aguardar pods estarem prontos
echo ""
echo -e "${YELLOW}⏳ Aguardando pods estarem prontos...${NC}"
microk8s kubectl wait --for=condition=ready pod -l app=memory-stress -n memory-stress-test --timeout=120s

echo ""
echo -e "${GREEN}=========================================="
echo "✓ Deploy concluído com sucesso!"
echo "==========================================${NC}"
echo ""
echo "Comandos úteis:"
echo ""
echo "  # Ver pods"
echo "  microk8s kubectl get pods -n memory-stress-test"
echo ""
echo "  # Ver logs"
echo "  microk8s kubectl logs -f deployment/memory-stress-app -n memory-stress-test"
echo ""
echo "  # Ver uso de recursos"
echo "  microk8s kubectl top pods -n memory-stress-test"
echo ""
echo "  # Ver HPA status"
echo "  microk8s kubectl get hpa -n memory-stress-test"
echo ""
echo "  # Deletar aplicação"
echo "  microk8s kubectl delete namespace memory-stress-test"
echo ""
echo "Monitorando logs (Ctrl+C para sair)..."
echo ""

# Mostrar logs
microk8s kubectl logs -f deployment/memory-stress-app -n memory-stress-test