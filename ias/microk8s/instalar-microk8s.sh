#!/bin/bash
cd ./microk8s


# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "🚀 HABILITANDO DASHBOARD DO MICROK8S"
    echo "=================================================="
    echo -e "${NC}"
}

# Função para verificar se o MicroK8s está instalado
check_microk8s() {
    print_status "Verificando se o MicroK8s está instalado..."
    if ! command -v microk8s &> /dev/null; then
        print_error "MicroK8s não está instalado! Instalando ... "
        sudo snap install microk8s --classic
        if [ $? -ne 0 ]; then
            print_error "Falha ao instalar o MicroK8s. Verifique sua conexão com a internet."
            exit 1
        fi                
    fi
    print_success "MicroK8s encontrado!"
}

# Função para verificar se o MicroK8s está rodando
check_microk8s_status() {
    print_status "Verificando status do MicroK8s..."
    if ! microk8s status --wait-ready --timeout=30 &> /dev/null; then
        print_error "MicroK8s não está rodando ou não está pronto!"
        print_status "Iniciando MicroK8s..."
        microk8s start
        microk8s status --wait-ready --timeout=60
    fi
    print_success "MicroK8s está rodando!"
}

# Função para habilitar o dashboard
enable_dashboard() {
    print_status "Habilitando o dashboard..."
    microk8s enable dashboard
    
    print_status "Aguardando pods do dashboard ficarem prontos..."
    microk8s kubectl wait --for=condition=ready pod -l k8s-app=kubernetes-dashboard -n kube-system --timeout=500s

    microk8s enable rbac
    microk8s enable metrics-server
    # microk8s enable observability

    if [ $? -eq 0 ]; then
        print_success "Dashboard habilitado com sucesso!"
    else
        print_error "Timeout aguardando pods do dashboard"
        exit 1
    fi
}

# Função para criar ServiceAccount com permissões admin
create_admin_user() {
    print_status "Criando usuário administrador..."
    
    # Verificar se já existe
    if microk8s kubectl get serviceaccount dashboard-admin -n kube-system &> /dev/null; then
        print_warning "ServiceAccount 'dashboard-admin' já existe"
    else
        microk8s kubectl create serviceaccount dashboard-admin -n kube-system
        print_success "ServiceAccount criado!"
    fi
    
    # Verificar se ClusterRoleBinding já existe
    if microk8s kubectl get clusterrolebinding dashboard-admin &> /dev/null; then
        print_warning "ClusterRoleBinding 'dashboard-admin' já existe"
    else
        microk8s kubectl create clusterrolebinding dashboard-admin \
          --clusterrole=cluster-admin \
          --serviceaccount=kube-system:dashboard-admin
        print_success "ClusterRoleBinding criado!"
    fi
}

# Função para gerar token
generate_token() {
    print_status "Gerando token de acesso..."
    TOKEN=$(microk8s kubectl create token dashboard-admin -n kube-system --duration=8760h 2>/dev/null)

    if [ -z "$TOKEN" ]; then
        print_error "Falha ao gerar token"
        exit 1
    fi
    print_success "Token gerado com sucesso!"
    return 0
}






# Função para iniciar port-forward
start_port_forward() {
    print_status "Verificando se port-forward já está ativo..."
    
    # Matar processos existentes na porta 10443
    if lsof -ti:10443 &> /dev/null; then
        print_warning "Porta 10443 já está em uso. Finalizando processos..."
        sudo kill -9 $(lsof -ti:10443) 2>/dev/null || true
        sleep 2
    fi
    
    print_status "Iniciando port-forward..."
    microk8s kubectl port-forward  --address 0.0.0.0 -n kube-system service/kubernetes-dashboard 10443:443 &
    PORT_FORWARD_PID=$!
    
    # Aguardar um pouco para o port-forward inicializar
    sleep 3
    
    # Verificar se o port-forward está funcionando
    if kill -0 $PORT_FORWARD_PID 2>/dev/null; then
        print_success "Port-forward iniciado (PID: $PORT_FORWARD_PID)"
        echo $PORT_FORWARD_PID > /tmp/microk8s-dashboard-pf.pid
    else
        print_error "Falha ao iniciar port-forward"
        exit 1
    fi
}

# Função para verificar conectividade
test_connectivity() {
    print_status "Testando conectividade com o dashboard..."
    
    # Aguardar um pouco mais
    sleep 5
    
    # Testar conexão HTTPS
    IP=$(ip -4 addr show ens33 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
    if curl -k -s https://$IP:10443 &> /dev/null; then
        print_success "Dashboard acessível via HTTPS!"
    else
        print_warning "Não foi possível testar a conectividade automaticamente"
        print_status "Isso pode ser normal - teste manualmente no navegador"
    fi
}

# Função para exibir informações finais
show_final_info() {
    echo ""
    echo -e "${GREEN}"
    echo "🎉 DASHBOARD CONFIGURADO COM SUCESSO!"
    echo "====================================="
    echo -e "${NC}"
    
    echo -e "${YELLOW}🔑 TOKEN DE ACESSO:${NC}"
    echo "======================================"
    echo "$TOKEN"
    echo "$TOKEN" > token.txt
    echo "======================================"
    echo ""
    
    echo -e "${YELLOW}🌐 COMO ACESSAR:${NC}"
    echo "1. Abra seu navegador"
    echo "2. Acesse: https://$IP:10443"
    echo "3. Aceite o certificado auto-assinado"
    echo "4. Selecione 'Token' como método de login"
    echo "5. Cole o token acima"
    echo "6. Clique em 'Sign In'"
    echo ""
    
    echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
    echo "- Use HTTPS (não HTTP)"
    echo "- O port-forward está rodando em background"
    echo "- Para parar: kill \$(cat /tmp/microk8s-dashboard-pf.pid)"
    echo "- Para reiniciar: execute este script novamente"
    echo ""
    
    echo -e "${BLUE}📋 COMANDOS ÚTEIS:${NC}"
    echo "- Verificar status: microk8s status"
    echo "- Ver pods: microk8s kubectl get pods -n kube-system"
    echo "- Novo token: microk8s kubectl create token dashboard-admin -n kube-system --duration=8760h"
    echo "- Parar port-forward: kill \$(cat /tmp/microk8s-dashboard-pf.pid)"
    echo ""
}

# Função para criar script de parada
create_stop_script() {
    cat > stop-dashboard.sh << 'EOF'
#!/bin/bash

echo "🛑 Parando dashboard do MicroK8s..."

# Parar port-forward
if [ -f /tmp/microk8s-dashboard-pf.pid ]; then
    PID=$(cat /tmp/microk8s-dashboard-pf.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Port-forward parado (PID: $PID)"
    else
        echo "⚠️  Port-forward já estava parado"
    fi
    rm -f /tmp/microk8s-dashboard-pf.pid
else
    echo "⚠️  Arquivo PID não encontrado"
fi

# Matar qualquer processo na porta 10443
if lsof -ti:10443 &> /dev/null; then
    sudo kill -9 $(lsof -ti:10443) 2>/dev/null
    echo "✅ Processos na porta 10443 finalizados"
fi

echo "🎯 Dashboard parado com sucesso!"
EOF

    chmod +x stop-dashboard.sh
    print_success "Script de parada criado: ./stop-dashboard.sh"
}

# Função principal
main() {
    print_header
    
    check_microk8s
    check_microk8s_status
    enable_dashboard
    create_admin_user
    generate_token
    start_port_forward
    test_connectivity
    create_stop_script
    show_final_info
}

# Tratamento de sinais para limpeza
cleanup() {
    print_warning "Interrompido pelo usuário"
    if [ ! -z "$PORT_FORWARD_PID" ]; then
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
    exit 1
}

trap cleanup SIGINT SIGTERM

# Executar função principal
main "$@"