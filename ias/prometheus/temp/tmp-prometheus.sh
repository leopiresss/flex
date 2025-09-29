# Criar configuração completa
cat > prometheus-new-config.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring  # Ajuste o namespace conforme necessário
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    rule_files:
      # - "first_rules.yml"
      # - "second_rules.yml"

    scrape_configs:
      # Job para o próprio Prometheus (ESSENCIAL)
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:9090']
        scrape_interval: 30s
        metrics_path: /metrics

      # Job para Node Exporter
      - job_name: 'node'
        static_configs:
          - targets: ['localhost:9100']
        scrape_interval: 30s

      # Job para cAdvisor
      - job_name: 'cadvisor'
        static_configs:
          - targets: ['localhost:8080']
        metrics_path: /metrics
        scrape_interval: 30s

      # Job para Kubelet (se disponível)
      - job_name: 'kubernetes-nodes-cadvisor'
        static_configs:
          - targets: ['localhost:10250']
        metrics_path: /metrics/cadvisor
        scheme: https
        tls_config:
          insecure_skip_verify: true
        scrape_interval: 30s
EOF

# Ajustar namespace se necessário
sed -i "s/namespace: monitoring/namespace: $PROMETHEUS_NAMESPACE/" prometheus-new-config.yaml

echo "✅ Nova configuração criada"

# Aplicar configuração
kubectl apply -f prometheus-new-config.yaml

# Verificar se foi aplicada
kubectl get configmap prometheus-config -n monitoring -o yaml | grep -A 5 "job_name.*prometheus"

echo "✅ Configuração aplicada"

# Reiniciar deployment para aplicar nova configuração
kubectl rollout restart deployment prometheus -n monitoring 

# Aguardar rollout completar
kubectl rollout status deployment prometheus -n monitoring --timeout=300s

echo "✅ Prometheus reiniciado"

# Aguardar Prometheus coletar dados (importante!)
echo "⏳ Aguardando coleta de dados (60 segundos)..."
sleep 60


# Testar prometheus_build_info
echo "🔍 Testando prometheus_build_info..."
result=$(curl -s "http://localhost:9090/api/v1/query?query=prometheus_build_info" | jq -r '.data.result | length')
echo "Resultados: $result"

if [[ "$result" -gt 0 ]]; then
    echo "✅ prometheus_build_info funcionando!"
    curl -s "http://localhost:9090/api/v1/query?query=prometheus_build_info" | jq '.data.result[0].metric'
else
    echo "❌ prometheus_build_info ainda vazio"
fi

# Testar outras métricas
echo -e "\n�� Testando outras métricas..."
curl -s "http://localhost:9090/api/v1/query?query=up" | jq '.data.result | length'
curl -s "http://localhost:9090/api/v1/query?query=prometheus_config_last_reload_successful" | jq '.data.result | length'