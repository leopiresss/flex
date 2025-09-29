#!/bin/bash

# Script para iniciar o servidor de números primos
# Uso: ./start_server.sh

echo "🚀 Iniciando Servidor de Números Primos"
echo "======================================"

PORT=7071
SCRIPT_NAME="prime_server.py"

# Verificar se o arquivo do servidor existe
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "❌ Arquivo $SCRIPT_NAME não encontrado!"
    echo "   Certifique-se de estar no diretório correto."
    exit 1
fi

# Verificar se a porta já está em uso
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Porta $PORT já está em uso!"
    echo "   Processo atual:"
    lsof -i :$PORT
    echo ""
    echo "🛠️  Deseja parar o processo atual e reiniciar? (s/N)"
    read -r response
    if [[ "$response" =~ ^([sS][iI]?[mM]?|[yY][eE]?[sS]?)$ ]]; then
        echo "   Parando processo na porta $PORT..."
        kill $(lsof -t -i:$PORT) 2>/dev/null
        sleep 2
        echo "   ✅ Processo parado"
    else
        echo "   Abortando..."
        exit 1
    fi
fi

# Verificar se Flask está instalado
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ Flask não encontrado!"
    echo "   Instalando Flask..."
    pip3 install flask
    if [ $? -ne 0 ]; then
        echo "   ❌ Erro ao instalar Flask"
        exit 1
    fi
    echo "   ✅ Flask instalado com sucesso"
fi

# Iniciar servidor
echo "🔥 Iniciando servidor na porta $PORT..."
echo "   Arquivo: $SCRIPT_NAME"
echo "   URL: http://localhost:$PORT"
echo ""
echo "📝 Para parar o servidor, pressione Ctrl+C"
echo "   Ou execute: kill \$(lsof -t -i:$PORT)"
echo ""
echo "🧪 Teste rápido após iniciar:"
echo "   curl \"http://localhost:$PORT/primes?count=5\""
echo ""
echo "Iniciando em 3 segundos..."
sleep 3

# Executar servidor
python3 "$SCRIPT_NAME"