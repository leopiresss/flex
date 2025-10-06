#!/bin/bash
#
# Script de monitoramento para o teste de stress
# Monitora logs, métricas e status do pod
#

URL="${1:-http://localhost:8080}"
INTERVAL="${2:-5}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    clear
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}   Memory Stress Test - Monitor em Tempo Real${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "URL: ${CYAN}$URL${NC} | Intervalo: ${CYAN}${INTERVAL}s${NC} | $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

# Verifica se curl está disponível
if ! command -v curl &> /dev/null; then
    echo "curl não está instalado!"
    exit 1
fi

# Verifica se jq está disponível
if command -v jq &> /dev/null; then
    JQ_CMD="jq -r"
else
    echo "Aviso: jq não instalado. Instale para melhor visualização."
    JQ_CMD="cat"
fi

while true; do
    print_header
    
    # Status da aplicação
    echo -e "${GREEN}┌─ Status da Aplicação${NC}"
    STATUS=$(curl -s "$URL/status" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        IS_RUNNING=$(echo "$STATUS" | jq -r '.is_running' 2>/dev/null || echo "N/A")
        CURRENT_MEM=$(echo "$STATUS" | jq -r '.current_memory_mb' 2>/dev/null || echo "N/A")
        CURRENT_PERC=$(echo "$STATUS" | jq -r '.current_memory_percent' 2>/dev/null || echo "N/A")
        TOTAL_MEM=$(echo "$STATUS" | jq -r '.total_system_memory_mb' 2>/dev/null || echo "N/A")
        TOTAL_LOGS=$(echo "$STATUS" | jq -r '.total_logs' 2>/dev/null || echo "N/A")
        
        echo -e "${YELLOW}│${NC} Estado:           ${CYAN}$([ "$IS_RUNNING" == "true" ] && echo "🟢 RODANDO" || echo "⚪ PARADO")${NC}"
        echo -e "${YELLOW}│${NC} Memória Atual:    ${CYAN}${CURRENT_MEM} MB (${CURRENT_PERC}%)${NC}"
        echo -e "${YELLOW}│${NC} Memória Total:    ${CYAN}${TOTAL_MEM} MB${NC}"
        echo -e "${YELLOW}│${NC} Total de Logs:    ${CYAN}${TOTAL_LOGS}${NC}"
        
        # Configuração do teste (se estiver rodando)
        if [ "$IS_RUNNING" == "true" ]; then
            TARGET_MEM=$(echo "$STATUS" | jq -r '.config.memory_mb' 2>/dev/null || echo "N/A")
            DURATION=$(echo "$STATUS" | jq -r '.config.duration_seconds' 2>/dev/null || echo "N/A")
            LOG_INTERVAL=$(echo "$STATUS" | jq -r '.config.log_interval_sec' 2>/dev/null || echo "N/A")
            
            echo -e "${YELLOW}│${NC}"
            echo -e "${YELLOW}│${NC} Config - Alvo:    ${CYAN}${TARGET_MEM} MB${NC}"
            echo -e "${YELLOW}│${NC} Config - Duração: ${CYAN}${DURATION}s${NC}"
            echo -e "${YELLOW}│${NC} Config - Log:     ${CYAN}a cada ${LOG_INTERVAL}s${NC}"
            
            # Barra de progresso de memória
            if [ "$TARGET_MEM" != "N/A" ] && [ "$CURRENT_MEM" != "N/A" ]; then
                PERCENT=$(echo "scale=0; ($CURRENT_MEM * 100) / $TARGET_MEM" | bc 2>/dev/null || echo "0")
                PERCENT=${PERCENT%.*}
                [ $PERCENT -gt 100 ] && PERCENT=100
                
                BAR_LENGTH=40
                FILLED=$(echo "scale=0; ($PERCENT * $BAR_LENGTH) / 100" | bc 2>/dev/null || echo "0")
                FILLED=${FILLED%.*}
                
                BAR="["
                for ((i=0; i<$BAR_LENGTH; i++)); do
                    if [ $i -lt $FILLED ]; then
                        BAR+="="
                    else
                        BAR+=" "
                    fi
                done
                BAR+="]"
                
                echo -e "${YELLOW}│${NC} Progresso:        ${CYAN}${BAR} ${PERCENT}%${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}│${NC} ${RED}✗ Não foi possível conectar à aplicação${NC}"
    fi
    echo -e "${GREEN}└────────────────────────────────────────────────────────${NC}"
    echo ""
    
    # Últimos logs
    echo -e "${GREEN}┌─ Últimos 5 Logs${NC}"
    LOGS=$(curl -s "$URL/logs?limit=5" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "$LOGS" | jq -r '.logs[] | "│ \(.timestamp) | \(.operation) | \(.memory_use_mb)MB | \(.message)"' 2>/dev/null | tail -5 || echo "│ Nenhum log disponível"
    else
        echo -e "${YELLOW}│${NC} ${RED}✗ Não foi possível obter logs${NC}"
    fi
    echo -e "${GREEN}└────────────────────────────────────────────────────────${NC}"
    echo ""
    
    # Métricas do Pod (se disponível)
    if command -v microk8s &> /dev/null; then
        echo -e "${GREEN}┌─ Métricas do Pod (Kubernetes)${NC}"
        POD_METRICS=$(microk8s kubectl top pod -l app=memory-stress-test --no-headers 2>/dev/null)
        
        if [ -n "$POD_METRICS" ]; then
            POD_NAME=$(echo "$POD_METRICS" | awk '{print $1}')
            POD_CPU=$(echo "$POD_METRICS" | awk '{print $2}')
            POD_MEM=$(echo "$POD_METRICS" | awk '{print $3}')
            
            echo -e "${YELLOW}│${NC} Pod:              ${CYAN}${POD_NAME}${NC}"
            echo -e "${YELLOW}│${NC} CPU:              ${CYAN}${POD_CPU}${NC}"
            echo -e "${YELLOW}│${NC} Memória (K8s):    ${CYAN}${POD_MEM}${NC}"
            
            # Status do pod
            POD_STATUS=$(microk8s kubectl get pod -l app=memory-stress-test --no-headers 2>/dev/null | awk '{print $3}')
            POD_RESTARTS=$(microk8s kubectl get pod -l app=memory-stress-test --no-headers 2>/dev/null | awk '{print $4}')
            
            echo -e "${YELLOW}│${NC} Status:           ${CYAN}${POD_STATUS}${NC}"
            echo -e "${YELLOW}│${NC} Restarts:         ${CYAN}${POD_RESTARTS}${NC}"
        else
            echo -e "${YELLOW}│${NC} ${RED}✗ Métricas não disponíveis (metrics-server pode não estar habilitado)${NC}"
        fi
        echo -e "${GREEN}└────────────────────────────────────────────────────────${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Pressione Ctrl+C para sair | Atualizando em ${INTERVAL}s...${NC}"
    
    sleep $INTERVAL
done