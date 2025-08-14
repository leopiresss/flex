#!/bin/bash
# Função para encontrar próxima porta livre
find_free_port() {
    local start_port=${1:-9090}
    local port=$start_port
    
    while ss -tlpn | grep -q ":$port "; do
        ((port++))
    done
    
    echo $port
}

