#!/bin/bash
# monitor.sh

echo "📊 Monitorando stress test Python..."

show_status() {
    echo "==================== STATUS PYTHON STRESS ===================="
    echo "🔍 Pods:"
    kubectl get pods -o wide | grep -E "(postgres|stress)"
    echo ""
    echo "📈 HPA:"
    kubectl get hpa stress-postgres-python-hpa
    echo ""
    echo "💾 Uso de recursos:"
    kubectl top pods | grep -E "(postgres|stress)"
    echo ""
    echo "🗄️ Status PostgreSQL:"
    kubectl exec deployment/postgres -- psql -U postgres -d stressdb -c "
        SELECT 
            'Conexões Ativas' as metric, 
            count(*) as value 
        FROM pg_stat_activity 
        WHERE state = 'active'
        UNION ALL
        SELECT 
            'Total Conexões', 
            count(*) 
        FROM pg_stat_activity;
    " 2>/dev/null || echo "❌ Erro ao conectar no PostgreSQL"
    echo ""
    echo "📊 Dados nas tabelas:"
    kubectl exec deployment/postgres -- psql -U postgres -d stressdb -c "
        SELECT 
            'stress_data' as tabela, 
            count(*) as registros 
        FROM stress_data 
        UNION ALL
        SELECT 
            'stress_logs', 
            count(*) 
        FROM stress_logs 
        UNION ALL
        SELECT 
            'stress_metrics', 
            count(*) 
        FROM stress_metrics;
    " 2>/dev/null || echo "❌ Tabelas ainda não criadas"
    echo ""
    echo "🔥 Últimos logs da aplicação:"
    kubectl logs --tail=5 deployment/stress-postgres-python 2>/dev/null || echo "❌ Pod ainda não está rodando"
    echo "=============================================================="
}

# Loop de monitoramento
while true; do
    clear
    show_status
    echo ""
    echo "⏰ Próxima atualização em 15 segundos... (Ctrl+C para sair)"
    sleep 15
done