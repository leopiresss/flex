#!/bin/bash


# Cores para impressão colorida
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

# Funções de mensagens
print_status()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success()   { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning()   { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()     { echo -e "${RED}[ERROR]${NC} $1"; }


# Função para iniciar port-forward parametrizado
start_port_forward() {
    print_status "Verificando se port-forward já está ativo na porta $LOCAL_PORT..."

    # Matar processos existentes na porta local
    if lsof -ti:"$LOCAL_PORT" &> /dev/null; then
        print_warning "Porta $LOCAL_PORT já está em uso. Finalizando processos..."
        sudo kill -9 $(lsof -ti:"$LOCAL_PORT") 2>/dev/null || true
        sleep 2
    fi

    print_status "Iniciando port-forward para $RESOURCE_TYPE/$RESOURCE_NAME ($NAMESPACE:$REMOTE_PORT -> $LOCAL_INTERFACE:$LOCAL_PORT)..."
    microk8s kubectl port-forward --address "$LOCAL_INTERFACE" -n "$NAMESPACE" "$RESOURCE_TYPE/$RESOURCE_NAME" "$LOCAL_PORT:$REMOTE_PORT" &
    PORT_FORWARD_PID=$!
    sleep 3

    if kill -0 $PORT_FORWARD_PID 2>/dev/null; then
        print_success "Port-forward iniciado (PID: $PORT_FORWARD_PID)"
        echo $PORT_FORWARD_PID > "$PID_FILE"
    else
        print_error "Falha ao iniciar port-forward"
        exit 1
    fi
}

# Função para testar conectividade HTTPS (opcional)
test_connectivity() {
    print_status "Testando conectividade HTTP ($LOCAL_INTERFACE:$LOCAL_PORT)..."
    sleep 5
    # Detecta IP automaticamente ou permite sobrescrever por variável
    IP=${LOCAL_IP:-$(ip -4 addr show ${NET_IFACE:$NET_IFACE} | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n 1)}
    if curl -k -s "http://$IP:$LOCAL_PORT" &> /dev/null; then
        print_success "Serviço acessível via HTTP!"
    else
        print_warning "Não foi possível testar conectividade automaticamente"
        print_status "Isso pode ser normal - teste manualmente no navegador"
    fi
}

# Exemplo de uso e leitura de parâmetros
usage() {
    echo "Uso: $0 <resource_type> <resource_name> <namespace> <local_port> <remote_port> [interface] [pid_file] [net_iface]"
    echo "Exemplo: $0 service my-service default 10443 443 0.0.0.0 /tmp/my-portfwd.pid eth0"
    exit 1
}

# MAIN





print_header()    {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "🚀 INICIANDO PORT-FORWARD ${RESOURCE_NOME_SISTEMA}"
    echo "=================================================="
    echo -e "${NC}"
}

# Leitura dos argumentos
RESOURCE_TYPE=${1:-service}
RESOURCE_NAME=${2:-kubernetes-dashboard}
NAMESPACE=${3:-kube-system}
LOCAL_PORT=${4:-10443}
REMOTE_PORT=${5:-443}
LOCAL_INTERFACE=${6:-0.0.0.0}
PID_FILE=${7:-/tmp/port-forward.pid}
NET_IFACE=${8:-ens33}
RESOURCE_NOME_SISTEMA=${9:-nome do sistema}



# Função principal recebendo todos os parâmetros necessários
executar_port_forward() {
    # Atribuição dos argumentos posicionais às variáveis
    RESOURCE_TYPE="$1"
    RESOURCE_NAME="$2"
    NAMESPACE="$3"
    LOCAL_PORT="$4"
    REMOTE_PORT="$5"
    LOCAL_INTERFACE="$6"
    PID_FILE="$7"
    NET_IFACE="$8"
    RESOURCE_NOME_SISTEMA="$9"

    print_header

    # Chamada das demais funções ou comandos usando as variáveis acima
    start_port_forward "$RESOURCE_TYPE" "$RESOURCE_NAME" "$NAMESPACE" "$LOCAL_PORT" "$REMOTE_PORT" "$LOCAL_INTERFACE" "$PID_FILE" "$RESOURCE_NOME_SISTEMA"
    test_connectivity "$LOCAL_PORT" "$NET_IFACE"

    ARQUIVO=~/flex/logs/log_urls.txt

    echo "$DATA_HORA - http://$IP:$LOCAL_PORT " >> "$ARQUIVO"
    DATA_HORA=$(date +"%Y-%m-%d %H:%M:%S")
    echo "" >> "$ARQUIVO"
    echo "_______________________________________________________________________________________" >> "$ARQUIVO"
    echo "$DATA_HORA - SISTEMA $RESOURCE_NOME_SISTEMA" >> "$ARQUIVO"
    echo "$DATA_HORA - http://$IP:$LOCAL_PORT " >> "$ARQUIVO"
    echo "$DATA_HORA - $RESOURCE_TYPE $RESOURCE_NAME $NAMESPACE $LOCAL_PORT $REMOTE_PORT $LOCAL_INTERFACE $PID_FILE" >> "$ARQUIVO"
    echo "_______________________________________________________________________________________"  >> "$ARQUIVO"   
     
}




