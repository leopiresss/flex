#!/bin/bash

echo "=== Instalando PostgreSQL Stress Test ==="

# Verificar se Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python3 não encontrado. Instalando..."
    sudo apt update
    sudo apt install -y python3 python3-pip
fi

# Instalar dependências Python
echo "Instalando dependências Python..."
pip3 install -r requirements.txt

# Criar diretórios necessários
mkdir -p logs
mkdir -p config

# Dar permissão de execução
chmod +x src/postgres_stress.py

echo "=== Instalação concluída ==="
echo ""
echo "Para executar:"
echo "  python3 src/postgres_stress.py"
echo ""
echo "Para configurar:"
echo "  Edite o arquivo config/database.conf"