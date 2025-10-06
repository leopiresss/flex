#!/bin/bash
#
# Script de limpeza e remoção
# Remove todos os recursos criados pela aplicação
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Função para confirmar ação
confirm() {
    read -p "$(echo -e ${YELLOW}$1 [y/N]:${NC} )" -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

print_section "Limpeza da Aplicação Memory Stress Test"

echo "Este script irá:"
echo "  1. Parar qualquer teste em execução"
echo "  2. Remover o deployment do Kubernetes"
echo "  3. Remover imagens Docker locais"
echo "  4. (Opcional) Remover completamente o MicroK8s"
echo ""

# Verifica se MicroK8s está instalado
if ! command -v microk8s &> /dev/null; then
    print_warn "MicroK8s não encontrado. Pulando limpeza do Kubernetes."
    MICROK8S_AVAILABLE=false
else
    MICROK8S_AVAILABLE=true
fi

# 1. Parar teste em execução
if [ "$MICROK8S_AVAILABLE" = true ]; then
    print_section "1. Parando Testes em Execução"
    
    POD_NAME=$(microk8s kubectl get pod -l app=memory-stress-test -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -n "$POD_NAME" ]; then
        print_info "Pod encontrado: $POD_NAME"
        print_info "Tentando parar teste via API..."
        
        # Tenta port-forward temporário
        microk8s kubectl port-forward pod/$POD_NAME 8080:8080 &
        PF_PID=$!
        sleep 2
        
        curl -X POST http://localhost:8080/stop 2>/dev/null || true
        curl -X POST http://localhost:8080/clear 2>/dev/null || true
        
        kill $PF_PID 2>/dev/null || true
        
        print_info "Teste parado."
    else
        print_info "Nenhum pod em execução encontrado."
    fi
fi

# 2. Remover recursos do Kubernetes
if [ "$MICROK8S_AVAILABLE" = true ]; then
    print_section "2. Removendo Recursos do Kubernetes"
    
    if confirm "Remover deployment e service do Kubernetes?"; then
        print_info "Removendo recursos..."
        
        microk8s kubectl delete -f microk8s-deployment.yaml --ignore-not-found=true 2>/dev/null || \
        microk8s kubectl delete deployment memory-stress-test --ignore-not-found=true 2>/dev/null
        
        microk8s kubectl delete service memory-stress-service --ignore-not-found=true 2>/dev/null
        
        print_info "Aguardando remoção completa..."
        sleep 5
        
        # Verifica se foi removido
        REMAINING=$(microk8s kubectl get pods -l app=memory-stress-test 2>/dev/null | wc -l)
        if [ $REMAINING -eq 0 ]; then
            print_info "Recursos removidos com sucesso!"
        else
            print_warn "Alguns recursos ainda estão sendo removidos..."
        fi
    else
        print_info "Mantendo recursos do Kubernetes."
    fi
fi

# 3. Remover imagens Docker
print_section "3. Removendo Imagens Docker"

if confirm "Remover imagens Docker da aplicação?"; then
    print_info "Removendo imagens..."
    
    # Remove imagem local
    docker rmi memory-stress-test:latest 2>/dev/null || print_warn "Imagem local não encontrada"
    
    # Remove imagem do registry do MicroK8s
    docker rmi localhost:32000/memory-stress-test:latest 2>/dev/null || print_warn "Imagem do registry não encontrada"
    
    print_info "Imagens removidas."
    
    if confirm "Limpar imagens Docker não utilizadas (prune)?"; then
        docker image prune -f
        print_info "Limpeza de imagens concluída."
    fi
else
    print_info "Mantendo imagens Docker."
fi

# 4. Remover arquivos gerados
print_section "4. Removendo Arquivos Gerados"

if confirm "Remover arquivos de log e métricas gerados?"; then
    print_info "Removendo arquivos..."
    
    rm -f logs_*.json 2>/dev/null || true
    rm -f test_*_logs.json 2>/dev/null || true
    rm -f metrics_*.csv 2>/dev/null || true
    rm -f latency_results.csv 2>/dev/null || true
    rm -f tree_statistics.json 2>/dev/null || true
    rm -f tree_results.json 2>/dev/null || true
    rm -f stress_logs.csv 2>/dev/null || true
    rm -f memory_data.csv 2>/dev/null || true
    rm -f memory_usage.png 2>/dev/null || true
    
    print_info "Arquivos removidos."
else
    print_info "Mantendo arquivos gerados."
fi

# 5. Opção de remover MicroK8s completamente
if [ "$MICROK8S_AVAILABLE" = true ]; then
    print_section "5. Remoção do MicroK8s (Opcional)"
    
    print_warn "ATENÇÃO: Esta ação irá remover COMPLETAMENTE o MicroK8s!"
    print_warn "Todos os deployments, serviços e dados serão perdidos!"
    echo ""
    
    if confirm "Deseja REMOVER COMPLETAMENTE o MicroK8s?"; then
        print_info "Parando MicroK8s..."
        microk8s stop
        
        print_info "Removendo MicroK8s..."
        sudo snap remove microk8s --purge
        
        print_info "Removendo grupo do usuário..."
        sudo delgroup microk8s 2>/dev/null || true
        
        print_info "MicroK8s removido completamente."
    else
        print_info "MicroK8s mantido."
        
        if confirm "Deseja apenas parar o MicroK8s?"; then
            microk8s stop
            print_info "MicroK8s parado."
        fi
    fi
fi

# Resumo final
print_section "Resumo da Limpeza"

echo ""
print_info "Limpeza concluída!"
echo ""

if [ "$MICROK8S_AVAILABLE" = true ]; then
    echo "Status do MicroK8s:"
    microk8s status 2>/dev/null || echo "  MicroK8s não está mais disponível"
    echo ""
fi

echo "Para reinstalar a aplicação:"
echo "  1. ./setup-microk8s.sh"
echo "  2. ./deploy-microk8s.sh"
echo ""

print_info "Obrigado por usar Memory Stress Test!"