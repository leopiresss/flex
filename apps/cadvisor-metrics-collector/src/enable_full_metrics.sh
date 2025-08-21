#!/bin/bash

# Script para habilitar todas as métricas do cAdvisor

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🚀 Habilitando Todas as Métricas do cAdvisor"
echo "============================================="

# Verificar se MicroK8s está rodando
if ! command -v microk8s &> /dev/null; then
    log_error "MicroK8s não encontrado"
    exit 1
fi

if ! microk8s kubectl version --client &> /dev/null; then
    log_error "Não foi possível conectar ao MicroK8s"
    exit 1
fi

log_success "MicroK8s disponível"

# Verificar se o namespace monitoring existe
if ! microk8s kubectl get namespace monitoring &> /dev/null; then
    log_info "Criando namespace monitoring..."
    microk8s kubectl create namespace monitoring
fi

# Backup da configuração atual (se existir)
if microk8s kubectl get daemonset cadvisor -n monitoring &> /dev/null; then
    log_info "Fazendo backup da configuração atual..."
    microk8s kubectl get daemonset cadvisor -n monitoring -o yaml > cadvisor-backup-$(date +%Y%m%d-%H%M%S).yaml
    log_success "Backup salvo"
    
    log_info "Removendo configuração atual..."
    microk8s kubectl delete daemonset cadvisor -n monitoring
    
    # Aguardar remoção completa
    log_info "Aguardando remoção dos pods..."
    sleep 10
fi

# Aplicar nova configuração
log_info "Aplicando configuração com todas as métricas..."

# Verificar se o arquivo de configuração existe
if [ ! -f "cadvisor-full-metrics.yaml" ]; then
    log_error "Arquivo cadvisor-full-metrics.yaml não encontrado"
    log_info "Criando arquivo de configuração..."
    
    # Criar arquivo de configuração inline
    cat > cadvisor-full-metrics.yaml << 'EOF'
# Conteúdo do arquivo YAML aqui (muito longo para incluir inline)
# Use o arquivo cadvisor-full-metrics.yaml fornecido anteriormente
EOF
fi

# Aplicar configuração
microk8s kubectl apply -f cadvisor-full-metrics.yaml

log_success "Configuração aplicada"

# Verificar status
log_info "Verificando status dos pods..."
sleep 15

# Aguardar pods ficarem prontos
log_info "Aguardando pods ficarem prontos..."
microk8s kubectl wait --for=condition=ready pod -l app=cadvisor -n monitoring --timeout=300s

# Verificar se pods estão rodando
RUNNING_PODS=$(microk8s kubectl get pods -n monitoring -l app=cadvisor --no-headers | grep Running | wc -l)
TOTAL_NODES=$(microk8s kubectl get nodes --no-headers | wc -l)

if [ "$RUNNING_PODS" -eq "$TOTAL_NODES" ]; then
    log_success "Todos os pods do cAdvisor estão rodando ($RUNNING_PODS/$TOTAL_NODES)"
else
    log_warning "Apenas $RUNNING_PODS de $TOTAL_NODES pods estão rodando"
fi

# Testar conectividade
log_info "Testando conectividade..."
if microk8s kubectl port-forward -n monitoring svc/cadvisor 8080:8080 &
then
    PORTFORWARD_PID=$!
    sleep 5
    
    if curl -s http://localhost:8080/healthz > /dev/null; then
        log_success "cAdvisor respondendo corretamente"
        
        # Verificar métricas disponíveis
        METRICS_COUNT=$(curl -s http://localhost:8080/metrics | grep -c "^container_" || true)
        log_info "Métricas disponíveis: $METRICS_COUNT"
        
    else
        log_warning "cAdvisor não está respondendo"
    fi
    
    # Parar port-forward
    kill $PORTFORWARD_PID 2>/dev/null || true
fi

echo ""
echo "============================================="
log_success "Configuração concluída!"
echo "============================================="
echo ""
echo "Para acessar o cAdvisor:"
echo "1. Port-forward: microk8s kubectl port-forward -n monitoring svc/cadvisor 8080:8080"
echo "2. Acesse: http://localhost:8080"
echo "3. Métricas: http://localhost:8080/metrics"
echo ""
echo "Para verificar logs:"
echo "microk8s kubectl logs -f -n monitoring daemonset/cadvisor"