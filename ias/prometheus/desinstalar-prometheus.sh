#!/bin/bash
# Desinstalando Prometheus e Alertmanager
source ~/flex/lib/port-lib.sh 

echo "🔥 INICIANDO DESINSTALAÇÃO DO PROMETHEUS E ALERTMANAGER"
echo "========================================================="

# Parâmetros para parar o port-forward
RESOURCE_TYPE="svc"
RESOURCE_NAME="prometheus-service"
NAMESPACE="monitoring"
LOCAL_PORT="9090"
REMOTE_PORT="9090"
LOCAL_INTERFACE="0.0.0.0"
PID_FILE="/tmp/cadivisor-pf.pid"
NET_IFACE="ens33"
RESOURCE_NOME_SISTEMA="PROMETHEUS"

echo "⚠️ - Parando port-forward do Prometheus..."
# Verificar se existe função para parar port-forward na biblioteca
if command -v parar_port_forward &> /dev/null; then
    parar_port_forward "$PID_FILE" "$RESOURCE_NOME_SISTEMA"
else
    # Alternativa manual para parar port-forward
    if [ -f "$PID_FILE" ]; then
        echo "⚠️ - Encontrado arquivo PID, terminando processo..."
        kill $(cat "$PID_FILE") 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    # Matar qualquer port-forward do prometheus na porta 9090
    pkill -f "port-forward.*prometheus-service.*9090" 2>/dev/null || true
fi

echo "⚠️ - Removendo StatefulSet do Alertmanager..."
kubectl delete -f alertmanager-statefulset.yaml -n monitoring --ignore-not-found=true

echo "⚠️ - Removendo ConfigMap do Alertmanager..."
kubectl delete -f configmap-alertmanager.yaml -n monitoring --ignore-not-found=true

echo "⚠️ - Removendo PersistentVolume do Alertmanager..."
kubectl delete -f alertmanager-pv.yaml --ignore-not-found=true

echo "⚠️ - Removendo StorageClass do Alertmanager..."
kubectl delete -f alertmanager-storageclass.yaml --ignore-not-found=true

echo "⚠️ - Removendo service do Prometheus..."
kubectl delete -f prometheus-service.yaml -n monitoring --ignore-not-found=true

echo "⚠️ - Removendo deployment do Prometheus..."
kubectl delete -f prometheus-deployment.yaml -n monitoring --ignore-not-found=true

echo "⚠️ - Removendo autenticação do Prometheus..."
kubectl delete -f prometheus-autenticacao.yaml -n monitoring --ignore-not-found=true

echo "⚠️ - Removendo configuração do Prometheus..."
kubectl delete -f prometheus-config.yaml -n monitoring --ignore-not-found=true

echo "⚠️ - Verificando recursos restantes no namespace monitoring..."
kubectl get all -n monitoring

echo "⚠️ - Verificando PVCs restantes..."
kubectl get pvc -n monitoring

echo "⚠️ - Removendo PVCs órfãos (se existirem)..."
kubectl delete pvc --all -n monitoring --ignore-not-found=true

echo "⚠️ - Aguardando finalização dos recursos..."
sleep 10

echo "⚠️ - Verificando se ainda existem pods em execução..."
PODS_RUNNING=$(kubectl get pods -n monitoring --no-headers 2>/dev/null | wc -l)
if [ "$PODS_RUNNING" -gt 0 ]; then
    echo "⚠️ - Forçando remoção de pods restantes..."
    kubectl delete pods --all -n monitoring --force --grace-period=0 --ignore-not-found=true
fi

echo "⚠️ - Removendo namespace monitoring..."
kubectl delete namespace monitoring --ignore-not-found=true

echo "⚠️ - Verificando se namespace foi removido..."
if kubectl get namespace monitoring &>/dev/null; then
    echo "❌ Namespace ainda existe, aguardando..."
    kubectl get namespace monitoring
else
    echo "✅ Namespace removido com sucesso"
fi

echo "⚠️ - Limpando arquivos PID restantes..."
rm -f /tmp/cadivisor-pf.pid
rm -f /tmp/prometheus-pf.pid

echo "⚠️ - Verificando processos port-forward restantes..."
PROMETHEUS_PF=$(pgrep -f "port-forward.*prometheus" || true)
if [ ! -z "$PROMETHEUS_PF" ]; then
    echo "⚠️ - Terminando processos port-forward restantes..."
    pkill -f "port-forward.*prometheus" || true
fi

echo ""
echo "🎯 VERIFICAÇÃO FINAL"
echo "==================="

echo "⚠️ - Verificando se ainda existem recursos do Prometheus..."
kubectl get all --all-namespaces | grep -E "(prometheus|alertmanager)" || echo "✅ Nenhum recurso encontrado"

echo "⚠️ - Verificando PVs relacionados ao Alertmanager..."
kubectl get pv | grep -E "(alertmanager|prometheus)" || echo "✅ Nenhum PV encontrado"

echo "⚠️ - Verificando StorageClasses relacionadas..."
kubectl get storageclass | grep -E "(alertmanager|prometheus)" || echo "✅ Nenhuma StorageClass encontrada"

echo ""
echo "🔥 DESINSTALAÇÃO CONCLUÍDA!"
echo "=========================="
echo "✅ Prometheus removido"
echo "✅ Alertmanager removido" 
echo "✅ Namespace monitoring removido"
echo "✅ Port-forwards finalizados"
echo "✅ Recursos de armazenamento limpos"
echo ""
echo "💡 Se você quiser reinstalar, execute o script de instalação novamente."