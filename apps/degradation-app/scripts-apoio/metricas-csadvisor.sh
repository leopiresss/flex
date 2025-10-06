echo "Listando métricas do cAdvisor no node: $NODE"
#!/bin/bash

# Obter um node
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

echo "Listando métricas do cAdvisor no node: $NODE"
echo "================================================"

# Listar métricas
kubectl get --raw /api/v1/nodes/$NODE/proxy/metrics/cadvisor | \
  grep "^container_" | \
  cut -d'{' -f1 | \
  sort -u | \
  nl

echo "================================================"
echo "Total de métricas encontradas: $(kubectl get --raw /api/v1/nodes/$NODE/proxy/metrics/cadvisor | grep '^container_' | cut -d'{' -f1 | sort -u | wc -l)"

# Pegar um node
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

# Verificar se a métrica existe
kubectl get --raw /api/v1/nodes/$NODE/proxy/metrics/cadvisor | grep "container_spec_memory_limit_bytes"