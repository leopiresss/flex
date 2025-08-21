# 1. Tornar scripts executáveis
chmod +x enable_full_metrics.sh
chmod +x check_metrics.py

# 2. Aplicar configuração completa
./enable_full_metrics.sh

# 3. Verificar métricas disponíveis
python3 check_metrics.py

# 4. Testar conectividade
microk8s kubectl port-forward -n monitoring svc/cadvisor 8080:8080 &
curl http://localhost:8080/metrics | grep -c "container_"