#!/bin/bash
#
# Script de teste para a aplicação de stress
# Uso: ./test-stress.sh [url]
#

# URL padrão (localhost com port-forward)
URL="${1:-http://localhost:8080}"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

# Verifica se curl está instalado
if ! command -v curl &> /dev/null; then
    echo "curl não está instalado!"
    exit 1
fi

# Verifica se jq está instalado
if ! command -v jq &> /dev/null; then
    echo "Aviso: jq não está instalado. Instale para melhor formatação dos resultados."
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

format_json() {
    if [ "$JQ_AVAILABLE" = true ]; then
        jq '.'
    else
        cat
    fi
}

print_section "1. Testando Health Check"
print_test "GET $URL/health"
curl -s "$URL/health" | format_json
echo ""

print_section "2. Verificando Status Inicial"
print_test "GET $URL/status"
curl -s "$URL/status" | format_json
echo ""

print_section "3. Testando com Memory MB (Fixo)"
print_info "Iniciando teste com 256 MB por 30 segundos..."
print_test "POST $URL/start"
curl -s -X POST "$URL/start" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_mb": 256,
    "duration_seconds": 30,
    "log_interval_sec": 5
  }' | format_json
echo ""

sleep 3

print_info "Verificando status após 3 segundos..."
curl -s "$URL/status" | format_json
echo ""

print_info "Aguardando 10 segundos para ver progresso..."
sleep 10

print_info "Status após 13 segundos..."
curl -s "$URL/status" | format_json
echo ""

print_info "Últimos 5 logs:"
curl -s "$URL/logs?limit=5" | format_json
echo ""

print_info "Aguardando teste finalizar..."
sleep 20

print_section "4. Testando com Memory Percent"
print_info "Iniciando teste com 30% da memória disponível por 20 segundos..."
print_test "POST $URL/start"
curl -s -X POST "$URL/start" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_percent": 30,
    "duration_seconds": 20,
    "log_interval_sec": 5
  }' | format_json
echo ""

sleep 5

print_info "Status durante execução..."
curl -s "$URL/status" | format_json
echo ""

print_info "Aguardando conclusão..."
sleep 18

print_section "5. Verificando Logs Completos"
print_test "GET $URL/logs"
print_info "Últimos 10 logs:"
curl -s "$URL/logs?limit=10" | format_json
echo ""

print_section "6. Limpando Memória"
print_test "POST $URL/clear"
curl -s -X POST "$URL/clear" | format_json
echo ""

sleep 2

print_info "Status após limpeza:"
curl -s "$URL/status" | format_json
echo ""

print_section "Testes Concluídos!"
print_info "Aplicação testada com sucesso!"
echo ""

print_info "Para monitorar o pod no Kubernetes:"
echo "  microk8s kubectl top pod -l app=memory-stress-test"
echo ""

print_info "Para ver logs do pod:"
echo "  microk8s kubectl logs -l app=memory-stress-test -f"
echo ""