#!/bin/bash

# Script para desinstalar o cAdvisor do MicroK8s
# Autor: Assistant
# Data: $(date +%Y-%m-%d)

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
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

# Função para verificar se o kubectl está disponível
check_kubectl() {
    if ! command -v microk8s &> /dev/null; then
        log_error "MicroK8s não encontrado. Certifique-se de que está instalado e no PATH."
        exit 1
    fi
    
    if ! sudo microk8s kubectl version --client &> /dev/null; then
        log_error "Não foi possível conectar ao cluster MicroK8s."
        exit 1
    fi
}

# Função para verificar se o namespace existe
check_namespace() {
    local namespace=$1
    if sudo microk8s kubectl get namespace "$namespace" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Função para verificar se um recurso existe
resource_exists() {
    local resource_type=$1
    local resource_name=$2
    local namespace=$3
    
    if [ -n "$namespace" ]; then
        sudo microk8s kubectl get "$resource_type" "$resource_name" -n "$namespace" &> /dev/null
    else
        sudo microk8s kubectl get "$resource_type" "$resource_name" &> /dev/null
    fi
}

# Função para deletar recurso com verificação
delete_resource() {
    local resource_type=$1
    local resource_name=$2
    local namespace=$3
    local description=$4
    
    if [ -n "$namespace" ]; then
        if resource_exists "$resource_type" "$resource_name" "$namespace"; then
            log_info "Removendo $description..."
            sudo microk8s kubectl delete "$resource_type" "$resource_name" -n "$namespace"
            log_success "$description removido com sucesso"
        else
            log_warning "$description não encontrado no namespace $namespace"
        fi
    else
        if resource_exists "$resource_type" "$resource_name"; then
            log_info "Removendo $description..."
            sudo microk8s kubectl delete "$resource_type" "$resource_name"
            log_success "$description removido com sucesso"
        else
            log_warning "$description não encontrado"
        fi
    fi
}

# Função para aguardar finalização da remoção
wait_for_deletion() {
    local resource_type=$1
    local resource_name=$2
    local namespace=$3
    local timeout=60
    local counter=0
    
    log_info "Aguardando finalização da remoção do $resource_type $resource_name..."
    
    while [ $counter -lt $timeout ]; do
        if [ -n "$namespace" ]; then
            if ! resource_exists "$resource_type" "$resource_name" "$namespace"; then
                log_success "$resource_type $resource_name removido completamente"
                return 0
            fi
        else
            if ! resource_exists "$resource_type" "$resource_name"; then
                log_success "$resource_type $resource_name removido completamente"
                return 0
            fi
        fi
        
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    
    echo ""
    log_warning "Timeout aguardando remoção do $resource_type $resource_name"
}

# Função principal de desinstalação
uninstall_cadvisor() {
    local namespace="monitoring"
    local force_remove=false
    
    # Parse argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--namespace)
                namespace="$2"
                shift 2
                ;;
            -f|--force)
                force_remove=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Opção desconhecida: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "Iniciando desinstalação do cAdvisor..."
    log_info "Namespace: $namespace"
    
    # Verificar se o namespace existe
    if ! check_namespace "$namespace"; then
        log_warning "Namespace '$namespace' não encontrado. Nada para remover."
        exit 0
    fi
    
    # 1. Remover ServiceMonitor (se existir)
    delete_resource "servicemonitor" "cadvisor" "$namespace" "ServiceMonitor do cAdvisor"
    
    # 2. Remover Service
    delete_resource "service" "cadvisor" "$namespace" "Service do cAdvisor"
    
    # 3. Remover DaemonSet
    delete_resource "daemonset" "cadvisor" "$namespace" "DaemonSet do cAdvisor"
    
    # Aguardar pods serem finalizados
    log_info "Aguardando finalização dos pods do cAdvisor..."
    sleep 5
    
    # Verificar se ainda existem pods
    if microk8s kubectl get pods -n "$namespace" -l app=cadvisor --no-headers 2>/dev/null | grep -q cadvisor; then
        log_warning "Ainda existem pods do cAdvisor. Aguardando finalização..."
        wait_for_deletion "pods" "-l app=cadvisor" "$namespace"
    fi
    
    # 4. Remover RBAC
    delete_resource "clusterrolebinding" "cadvisor" "" "ClusterRoleBinding do cAdvisor"
    delete_resource "clusterrole" "cadvisor" "" "ClusterRole do cAdvisor"
    delete_resource "serviceaccount" "cadvisor" "$namespace" "ServiceAccount do cAdvisor"
    
    # 5. Perguntar sobre remoção do namespace (se não for default)
    if [ "$namespace" != "default" ] && [ "$namespace" != "kube-system" ]; then
        # Verificar se existem outros recursos no namespace
        local other_resources=$(microk8s kubectl get all -n "$namespace" --no-headers 2>/dev/null | wc -l)
        
        if [ "$other_resources" -eq 0 ] || [ "$force_remove" = true ]; then
            if [ "$force_remove" = true ] || ask_confirmation "Remover o namespace '$namespace'? (Isso removerá TODOS os recursos do namespace)"; then
                delete_resource "namespace" "$namespace" "" "Namespace $namespace"
            fi
        else
            log_info "Namespace '$namespace' contém outros recursos. Mantendo o namespace."
        fi
    fi
    
    log_success "Desinstalação do cAdvisor concluída!"
}

# Função para mostrar ajuda
show_help() {
    cat << EOF
Script de Desinstalação do cAdvisor para MicroK8s

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -n, --namespace NAMESPACE    Namespace onde o cAdvisor está instalado (default: monitoring)
    -f, --force                  Força a remoção sem confirmações
    -h, --help                   Mostra esta mensagem de ajuda

EXAMPLES:
    $0                          # Remove do namespace 'monitoring'
    $0 -n kube-system          # Remove do namespace 'kube-system'
    $0 -f                      # Remove forçadamente sem confirmações
    $0 -n monitoring -f        # Remove do namespace 'monitoring' forçadamente

EOF
}

# Função para confirmação
ask_confirmation() {
    local message="$1"
    while true; do
        read -p "$message [y/N]: " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            "" ) return 1;;
            * ) echo "Por favor, responda sim (y) ou não (n).";;
        esac
    done
}

# Função de limpeza em caso de erro
cleanup_on_error() {
    log_error "Erro durante a desinstalação. Verificando estado atual..."
    
    # Listar recursos restantes relacionados ao cAdvisor
    log_info "Recursos restantes relacionados ao cAdvisor:"
    
    echo "=== Pods ==="
    sudo microk8s kubectl get pods --all-namespaces -l app=cadvisor 2>/dev/null || echo "Nenhum pod encontrado"
    
    echo "=== Services ==="
    sudo microk8s kubectl get services --all-namespaces -l app=cadvisor 2>/dev/null || echo "Nenhum service encontrado"
    
    echo "=== DaemonSets ==="
    sudo microk8s kubectl get daemonsets --all-namespaces -l app=cadvisor 2>/dev/null || echo "Nenhum daemonset encontrado"
    
    echo "=== RBAC ==="
    sudo microk8s kubectl get clusterrole cadvisor 2>/dev/null || echo "ClusterRole não encontrado"
    sudo microk8s kubectl get clusterrolebinding cadvisor 2>/dev/null || echo "ClusterRoleBinding não encontrado"
}

# Trap para capturar erros
trap cleanup_on_error ERR

# Função principal
main() {
    echo "=================================================="
    echo "    Script de Desinstalação do cAdvisor"
    echo "=================================================="
    echo ""
    
    # Verificar pré-requisitos
    log_info "Verificando pré-requisitos..."
    check_kubectl
    log_success "MicroK8s disponível e funcionando"
    
    # Executar desinstalação
    uninstall_cadvisor "$@"
    
    echo ""
    echo "=================================================="
    log_success "Desinstalação concluída com sucesso!"
    echo "=================================================="
}

# Executar script principal se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi