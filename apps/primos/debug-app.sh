#!/bin/bash

# Script para debuggar problemas na aplicação prime-server

echo "=== DEBUG APLICAÇÃO PRIME-SERVER ==="
echo ""

# 1. Remover deployment anterior com problemas
echo "1. Limpando deployment anterior..."
microk8s kubectl delete deployment prime-server -n default --ignore-not-found=true
sleep 5

# 2. Aplicar deployment sem health checks
echo ""
echo "2. Aplicando deployment sem health checks..."
microk8s kubectl apply -f deployment-no-health.yaml

# 3. Aguardar pod iniciar
echo ""
echo "3. Aguardando pod iniciar..."
sleep 10

# 4. Verificar status do pod
echo ""
echo "4. Status do pod:"
microk8s kubectl get pods -l app=prime-server -n default

# 5. Ver logs da aplicação
echo ""
echo "5. Logs da aplicação:"
POD_NAME=$(microk8s kubectl get pods -l app=prime-server -n default -o jsonpath='{.items[0].metadata.name}')
if [ ! -z "$POD_NAME" ]; then
    echo "Pod: $POD_NAME"
    echo "--- LOGS ---"
    microk8s kubectl logs $POD_NAME -n default --tail=20
    echo "--- FIM LOGS ---"
else
    echo "❌ Nenhum pod encontrado"
    exit 1
fi

# 6. Verificar se o pod está rodando
echo ""
echo "6. Detalhes do pod:"
microk8s kubectl describe pod $POD_NAME -n default | head -30

# 7. Testar conectividade dentro do pod
echo ""
echo "7. Testando conectividade dentro do pod..."

# Verificar se a aplicação está escutando na porta 7070
echo "Verificando portas abertas no pod:"
microk8s kubectl exec $POD_NAME -n default -- netstat -tlnp 2>/dev/null || \
microk8s kubectl exec $POD_NAME -n default -- ss -tlnp 2>/dev/null || \
echo "Comando netstat/ss não disponível no container"

# Testar curl dentro do pod
echo ""
echo "Testando curl localhost:7070 dentro do pod:"
microk8s kubectl exec $POD_NAME -n default -- curl -s http://localhost:7070 2>/dev/null || \
echo "❌ Aplicação não responde em localhost:7070"

# Testar diferentes caminhos
echo ""
echo "Testando diferentes endpoints:"
for path in "/" "/health" "/status" "/ping" "/api/health"; do
    echo -n "  $path: "
    if microk8s kubectl exec $POD_NAME -n default -- curl -s -o /dev/null -w "%{http_code}" http://localhost:7070$path 2>/dev/null; then
        echo " ✓"
    else
        echo " ❌"
    fi
done

# 8. Testar acesso externo
echo ""
echo "8. Testando acesso externo via NodePort:"
echo "Aguardando 5 segundos para service estar pronto..."
sleep 5

if curl -s -o /dev/null -w "%{http_code}" http://localhost:30080 2>/dev/null | grep -q "200\|404\|500"; then
    echo "✓ Service responde via NodePort"
    echo "Resposta:"
    curl -s http://localhost:30080 || echo "Sem resposta body"
else
    echo "❌ Service não responde via NodePort"
fi

# 9. Informações de debug
echo ""
echo "9. Informações para debug:"
echo ""
echo "Dockerfile da aplicação:"
if [ -f "Dockerfile" ]; then
    echo "EXPOSE encontrado:"
    grep -i "EXPOSE" Dockerfile || echo "Nenhuma porta EXPOSE encontrada"
    echo ""
    echo "CMD/ENTRYPOINT:"
    grep -E "^(CMD|ENTRYPOINT)" Dockerfile || echo "Comando de inicialização não encontrado"
else
    echo "❌ Dockerfile não encontrado no diretório atual"
fi

echo ""
echo "=== RESUMO ==="
echo ""
echo "Para resolver os problemas:"
echo "1. Verifique os logs acima para erros na aplicação"
echo "2. Confirme que a aplicação roda na porta 7070"
echo "3. Verifique se existe endpoint /health (ou remova health checks)"
echo "4. Teste localmente: docker run -p 7070:7070 prime-server:latest"
echo ""
echo "Comandos úteis:"
echo "  - Ver logs:     microk8s kubectl logs -f $POD_NAME"
echo "  - Exec no pod:  microk8s kubectl exec -it $POD_NAME -- /bin/sh"
echo "  - Port forward: microk8s kubectl port-forward $POD_NAME 7070:7070"