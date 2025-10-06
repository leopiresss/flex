#!/bin/bash
#
# Script de configuração inicial do MicroK8s
# Prepara o ambiente para executar a aplicação
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "Setup MicroK8s para Memory Stress Test"
echo "=========================================="
echo ""

# Verifica se está rodando como root para instalação
if [[ $EUID -eq 0 ]] && [[ "$1" != "--install" ]]; then
   print_error "Este script não deve ser executado como root (exceto com --install)"
   echo "Use: ./setup-microk8s.sh"
   exit 1
fi

# Instalação do MicroK8s (opcional)
if [[ "$1" == "--install" ]]; then
    print_info "Instalando MicroK8s..."
    
    if command -v microk8s &> /dev/null; then
        print_warn "MicroK8s já está instalado!"
    else
        sudo snap install microk8s --classic
        print_info "MicroK8s instalado!"
    fi
    
    print_info "Adicionando usuário ao grupo microk8s..."
    sudo usermod -a -G microk8s $USER
    sudo chown -f -R $USER ~/.kube
    
    print_warn "IMPORTANTE: Faça logout e login novamente para aplicar as permissões do grupo!"
    print_warn "Depois execute: ./setup-microk8s.sh (sem --install)"
    exit 0
fi

# Verifica instalação
print_info "Verificando instalação do MicroK8s..."
if ! command -v microk8s &> /dev/null; then
    print_error "MicroK8s não encontrado!"
    echo ""
    echo "Execute para instalar:"
    echo "  sudo ./setup-microk8s.sh --install"
    exit 1
fi

# Inicia o MicroK8s se não estiver rodando
print_info "Verificando status do MicroK8s..."
if ! microk8s status --wait-ready &> /dev/null; then
    print_warn "MicroK8s não está rodando. Iniciando..."
    microk8s start
    sleep 5
fi

print_info "Aguardando MicroK8s ficar pronto..."
microk8s status --wait-ready

# Habilita addons necessários
print_info "Habilitando addons essenciais..."

print_info "  - dns (resolução de nomes)"
microk8s enable dns

print_info "  - storage (volumes persistentes)"
microk8s enable storage

print_info "  - registry (registry local)"
microk8s enable registry

print_info "  - metrics-server (monitoramento)"
microk8s enable metrics-server

print_info "Aguardando addons ficarem prontos..."
sleep 10

# Verifica addons
print_info "Addons habilitados:"
microk8s status | grep -A 20 "addons:"

echo ""
print_info "Configurando alias kubectl..."
if ! grep -q "alias kubectl='microk8s kubectl'" ~/.bashrc; then
    echo "alias kubectl='microk8s kubectl'" >> ~/.bashrc
    print_info "Alias adicionado ao ~/.bashrc"
fi

echo ""
print_info "Verificando versão do Kubernetes..."
microk8s kubectl version --short

echo ""
print_info "Verificando nodes..."
microk8s kubectl get nodes

echo ""
print_info "Verificando namespaces..."
microk8s kubectl get namespaces

echo ""
echo "=========================================="
print_info "Setup concluído com sucesso!"
echo "=========================================="
echo ""

print_info "Próximos passos:"
echo "  1. Execute o script de deploy:"
echo "     ./deploy-microk8s.sh"
echo ""
echo "  2. Ou faça deploy manual:"
echo "     docker build -t localhost:32000/memory-stress-test:latest ."
echo "     docker push localhost:32000/memory-stress-test:latest"
echo "     microk8s kubectl apply -f microk8s-deployment.yaml"
echo ""

print_info "Comandos úteis:"
echo "  Status:        microk8s status"
echo "  Parar:         microk8s stop"
echo "  Iniciar:       microk8s start"
echo "  Dashboard:     microk8s dashboard-proxy"
echo "  kubectl:       microk8s kubectl <comando>"
echo ""

print_info "Para usar 'kubectl' diretamente (sem microk8s):"
echo "  source ~/.bashrc"
echo "  ou reabra o terminal"
echo ""