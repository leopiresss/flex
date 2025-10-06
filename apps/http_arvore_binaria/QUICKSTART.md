# 🚀 Guia de Início Rápido

Este guia vai te colocar operacional em menos de 5 minutos!

## ⚡ Instalação em 3 Passos

### Passo 1: Preparar o Ambiente

```bash
# Clonar ou baixar os arquivos do projeto
cd memory-stress-test

# Tornar scripts executáveis
chmod +x *.sh
```

### Passo 2: Instalar MicroK8s (primeira vez)

```bash
# Instalar MicroK8s
sudo ./setup-microk8s.sh --install

# IMPORTANTE: Fazer logout e login novamente
# Depois executar:
./setup-microk8s.sh
```

### Passo 3: Deploy da Aplicação

```bash
# Deploy automático (build + push + apply)
./deploy-microk8s.sh
```

## 🎯 Primeiro Teste

### Terminal 1: Port Forward

```bash
microk8s kubectl port-forward svc/memory-stress-service 8080:8080
```

### Terminal 2: Executar Teste

```bash
# Teste rápido com 30% de memória por 60 segundos
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{
    "memory_percent": 30,
    "duration_seconds": 60,
    "log_interval_sec": 10
  }'

# Verificar status
curl http://localhost:8080/status | jq
```

### Terminal 3: Monitorar

```bash
./monitor-stress.sh
```

## 📊 Comandos Essenciais

### Verificar Status

```bash
# Status da aplicação
curl http://localhost:8080/status | jq

# Status do pod
microk8s kubectl get pods -l app=memory-stress-test

# Métricas do pod
microk8s kubectl top pod -l app=memory-stress-test
```

### Ver Logs

```bash
# Logs da aplicação
curl http://localhost:8080/logs | jq

# Logs do pod
microk8s kubectl logs -l app=memory-stress-test -f
```

### Parar e Limpar

```bash
# Parar teste
curl -X POST http://localhost:8080/stop

# Limpar memória
curl -X POST http://localhost:8080/clear
```

## 🧪 Testes Prontos

### Teste 1: Memória Fixa (512 MB)

```bash
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{
    "memory_mb": 512,
    "duration_seconds": 120,
    "log_interval_sec": 15
  }'
```

### Teste 2: Percentual (50%)

```bash
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{
    "memory_percent": 50,
    "duration_seconds": 180,
    "log_interval_sec": 20
  }'
```

### Teste 3: Stress Intenso (80%)

```bash
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{
    "memory_percent": 80,
    "duration_seconds": 300,
    "log_interval_sec": 10
  }'
```

## 🔧 Scripts Auxiliares

### Suite de Testes Automatizada

```bash
./test-stress.sh
```

### Monitor em Tempo Real

```bash
# Monitor local (port-forward ativo)
./monitor-stress.sh

# Monitor remoto via NodePort
./monitor-stress.sh http://NODE_IP:30080
```

### Limpeza Completa

```bash
./cleanup.sh
```

## 📈 Cenários Comuns de Pesquisa

### Cenário 1: Teste de Escalabilidade

**Objetivo:** Encontrar o limite de memória antes de OOMKill

```bash
# Teste progressivo
for PERC in 20 40 60 80 90; do
  echo "Testando ${PERC}%..."
  curl -X POST http://localhost:8080/start \
    -H "Content-Type: application/json" \
    -d "{\"memory_percent\": $PERC, \"duration_seconds\": 60, \"log_interval_sec\": 10}"
  sleep 65
  curl -X POST http://localhost:8080/clear
  sleep 5
done
```

### Cenário 2: Análise de Comportamento

**Objetivo:** Coletar dados para análise posterior

```bash
# Teste longo com coleta de métricas
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{
    "memory_percent": 60,
    "duration_seconds": 600,
    "log_interval_sec": 30
  }'

# Salvar logs periodicamente
for i in {1..20}; do
  sleep 30
  curl -s http://localhost:8080/logs > "logs_snapshot_${i}.json"
done
```

### Cenário 3: Comparação de Configurações

**Objetivo:** Comparar diferentes configurações de memória

```bash
# Teste A: 256 MB fixo
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{"memory_mb": 256, "duration_seconds": 120, "log_interval_sec": 10}'
sleep 125
curl -s http://localhost:8080/logs > test_256mb.json
curl -X POST http://localhost:8080/clear
sleep 10

# Teste B: 50% memória
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{"memory_percent": 50, "duration_seconds": 120, "log_interval_sec": 10}'
sleep 125
curl -s http://localhost:8080/logs > test_50percent.json
curl -X POST http://localhost:8080/clear
```

## 🐛 Troubleshooting Rápido

### Pod não inicia

```bash
# Ver eventos
microk8s kubectl describe pod -l app=memory-stress-test

# Ver logs
microk8s kubectl logs -l app=memory-stress-test
```

### OOMKilled

```bash
# Aumentar limite de memória
# Editar microk8s-deployment.yaml:
# resources.limits.memory: "4Gi"

# Reaplicar
microk8s kubectl apply -f microk8s-deployment.yaml
```

### Aplicação não responde

```bash
# Verificar health
curl http://localhost:8080/health

# Reiniciar pod
microk8s kubectl rollout restart deployment/memory-stress-test
```

### Imagem não encontrada

```bash
# Rebuild e push
docker build -t localhost:32000/memory-stress-test:latest .
docker push localhost:32000/memory-stress-test:latest

# Reiniciar deployment
microk8s kubectl rollout restart deployment/memory-stress-test
```

## 📚 Próximos Passos

Depois de dominar o básico:

1. Leia o [README.md](README.md) completo para detalhes técnicos
2. Explore o [EXAMPLES.md](EXAMPLES.md) para casos de uso avançados
3. Configure monitoramento com Prometheus/Grafana
4. Integre com ferramentas de CI/CD para testes automatizados

## 💡 Dicas Importantes

1. **Sempre monitore**: Use `./monitor-stress.sh` durante testes
2. **Limpe memória**: Execute `curl -X POST http://localhost:8080/clear` após cada teste
3. **Ajuste limites**: Configure `resources.limits.memory` no deployment conforme necessário
4. **Use percentual**: Para ambientes dinâmicos, prefira `memory_percent` ao invés de `memory_mb`
5. **Salve logs**: Exporte logs importantes antes de iniciar novo teste

## ⚠️ Avisos

- ⚠️ Use apenas em ambientes de teste/desenvolvimento
- ⚠️ Não execute em produção sem supervisão
- ⚠️ Configure limites apropriados de recursos
- ⚠️ Monitore o impacto no cluster

## 🆘 Precisa de Ajuda?

```bash
# Ver todos os endpoints disponíveis
curl http://localhost:8080/

# Ver documentação completa
cat README.md

# Ver exemplos práticos
cat EXAMPLES.md
```

---

**Pronto!** Você está pronto para realizar testes de stress de memória no Kubernetes! 🎉