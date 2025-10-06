#!/bin/bash

# Constants
MAX_RETRIES=3
WAIT_TIME=5
PORT=8070
NAMESPACE="monitoring"
SERVICE="cadvisor"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check if port is in use
check_port() {
    if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}[ERROR] Port ${PORT} is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to start port-forward with retry
start_port_forward() {
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        echo -e "${BLUE}[INFO] Attempting port-forward (attempt $((retry_count+1))/${MAX_RETRIES})${NC}"
        
        # Kill any existing port-forward on the same port
        pkill -f "port-forward.*:${PORT}"
        
        # Start port-forward
        kubectl port-forward -n ${NAMESPACE} svc/${SERVICE} ${PORT}:${PORT} --address 0.0.0.0 &
        PID=$!
        
        # Wait for port-forward to establish
        sleep 3
        
        # Test connection
        if curl -s http://localhost:${PORT}/metrics > /dev/null; then
            echo -e "${GREEN}[SUCCESS] Port-forward established successfully${NC}"
            echo -e "${BLUE}[INFO] Service accessible at http://localhost:${PORT}${NC}"
            return 0
        else
            echo -e "${RED}[ERROR] Port-forward failed${NC}"
            kill $PID 2>/dev/null
            ((retry_count++))
            sleep $WAIT_TIME
        fi
    done
    
    echo -e "${RED}[ERROR] Max retries reached. Port-forward failed${NC}"
    return 1
}

# Main execution
if check_port; then
    start_port_forward
fi