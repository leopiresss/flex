#!/bin/bash

echo "🚀 Instalando Pod Metrics Collector"
echo "==================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Instalar dependências
echo "📦 Instalando dependências..."
pip3 install requests pandas openpyxl

# Tornar scripts executáveis
chmod +x pod_metrics_collector.py
chmod +x quick_pod_metrics.py

echo "✅ Instalação concluída!"
echo ""
echo "Uso:"
echo "1. Básico: python3 quick_pod_metrics.py cpu-stress-job-l9rxd"
echo "2. Completo: python3 pod_metrics_collector.py cpu-stress-job-l9rxd --output metrics.csv"
echo "3. Contínuo: python3 pod_metrics_collector.py cpu-stress-job-l9rxd --continuous --interval 10"