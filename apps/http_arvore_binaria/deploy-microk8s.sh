
#!/bin/bash
#
# Script de deploy para MicroK8s
# Stress Test de Memória com Árvore Binária
#

set -e

echo "=========================================="
echo "Deploy Memory Stress Test - MicroK8s"
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verifica se o MicroK8s está instalado
print_info "Verificando instalação do MicroK8s..."
if ! command -v microk8s &> /dev/null; then
    print_error "MicroK8s não está instalado!"
    echo "Instale com: sudo snap install microk8s --classic"
    exit 1
fi

print_info "MicroK8s encontrado!"

# Verifica se o MicroK8s está rodando
print_info "Verificando status do MicroK8s..."
if ! microk8s status --wait-ready &> /dev/null; then
    print_error "MicroK8s não está rodando!"
    echo "Inicie com: microk8s start"
    exit 1
fi

print_info "MicroK8s está rodando!"

# Habilita addons necessários
print_info "Habilitando addons necessários..."
microk8s enable dns storage registry

print_info "Aguardando addons ficarem prontos..."
sleep 5

# Constrói a imagem Docker
print_info "Construindo imagem Docker..."
docker build -t localhost:32000/memory-stress-test:latest .

if [ $? -eq 0 ]; then
    print_info "Imagem construída com sucesso!"
else
    print_error "Falha ao construir imagem!"
    exit 1
fi

# Faz push para o registry local do MicroK8s
print_info "Enviando imagem para registry local do MicroK8s..."
docker push localhost:32000/memory-stress-test:latest

if [ $? -eq 0 ]; then
    print_info "Imagem enviada com sucesso!"
else
    print_error "Falha ao enviar imagem!"
    exit 1
fi

# Remove deployment anterior se existir
print_info "Removendo deployment anterior (se existir)..."
microk8s kubectl delete -f microk8s-deployment.yaml --ignore-not-found=true

print_info "Aguardando remoção completa..."
sleep 5

# Aplica o novo deployment
print_info "Aplicando deployment no MicroK8s..."
microk8s kubectl apply -f microk8s-deployment.yaml

if [ $? -eq 0 ]; then
    print_info "Deployment aplicado com sucesso!"
else
    print_error "Falha ao aplicar deployment!"
    exit 1
fi

# Aguarda o pod ficar pronto
print_info "Aguardando pod ficar pronto..."
microk8s kubectl wait --for=condition=ready pod -l app=memory-stress-test --timeout=120s

if [ $? -eq 0 ]; then
    print_info "Pod está pronto!"
else
    print_warn "Timeout aguardando pod. Verifique com: microk8s kubectl get pods"
fi

# Mostra informações do deployment
echo ""
echo "=========================================="
print_info "Deploy concluído com sucesso!"
echo "=========================================="
echo ""

print_info "Status dos pods:"
microk8s kubectl get pods -l app=memory-stress-test

echo ""
print_info "Status do service:"
microk8s kubectl get svc memory-stress-service

echo ""
print_info "Para acessar a aplicação:"
echo "  1. Port forward:"
echo "     microk8s kubectl port-forward svc/memory-stress-service 8080:8080"
echo ""
echo "  2. Acessar via NodePort:"
NODE_IP=$(hostname -I | awk '{print $1}')
echo "     http://${NODE_IP}:30080"
echo ""

print_info "Para visualizar logs:"
echo "  microk8s kubectl logs -l app=memory-stress-test -f"
echo ""

print_info "Para testar:"
echo "  curl http://localhost:8080/health"
echo ""

echo "=========================================="
print_info "Comandos úteis:"
echo "=========================================="
echo "Ver pods:      microk8s kubectl get pods"
echo "Ver logs:      microk8s kubectl logs -l app=memory-stress-test -f"
echo "Ver detalhes:  microk8s kubectl describe pod -l app=memory-stress-test"
echo "Deletar:       microk8s kubectl delete -f microk8s-deployment.yaml"
echo "Reiniciar:     microk8s kubectl rollout restart deployment/memory-stress-test"
echo ""