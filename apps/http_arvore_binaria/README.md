# Stress Test de Memória para Kubernetes

Aplicação Python para testes de stress de memória em pods Kubernetes utilizando estrutura de árvore binária.

## 📋 Características

- ✅ Geração de stress de memória controlado
- ✅ Algoritmo de árvore binária para consumo de memória
- ✅ Duas rotinas: construção da árvore e pesquisa
- ✅ Parâmetros configuráveis (memória fixa ou percentual, duração, intervalo de log)
- ✅ Logs com timestamp e uso de memória
- ✅ API HTTP para controle remoto
- ✅ Pronto para Kubernetes com health checks
- ✅ Scripts automatizados para MicroK8s

## 🚀 Deploy no MicroK8s (Recomendado)

### Instalação Rápida

```bash
# 1. Tornar scripts executáveis
chmod +x *.sh

# 2. Instalar e configurar MicroK8s (primeira vez)
sudo ./setup-microk8s.sh --install
# Faça logout e login novamente

# 3. Configurar addons e verificar instalação
./setup-microk8s.sh

# 4. Deploy automático da aplicação
./deploy-microk8s.sh

# 5. Testar a aplicação
./test-stress.sh

# 6. Monitorar em tempo real
./monitor-stress.sh
```

### Deploy Manual no MicroK8s

```bash
# Construir e enviar imagem
docker build -t localhost:32000/memory-stress-test:latest .
docker push localhost:32000/memory-stress-test:latest

# Deploy
microk8s kubectl apply -f microk8s-deployment.yaml

# Verificar
microk8s kubectl get pods -l app=memory-stress-test
microk8s kubectl get svc memory-stress-service

# Port forward
microk8s kubectl port-forward svc/memory-stress-service 8080:8080
```

## 📡 Endpoints da API

### Iniciar teste de stress (Memória Fixa)

```bash
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{
    "memory_mb": 500,
    "duration_seconds": 120,
    "log_interval_sec": 10
  }'
```

### Iniciar teste de stress (Percentual de Memória) **NOVO!**

```bash
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{
    "memory_percent": 50,
    "duration_seconds": 120,
    "log_interval_sec": 10
  }'
```

**Parâmetros:**
- `memory_mb`: Memória alvo em MB (10-10000) - **exclusivo com memory_percent**
- `memory_percent`: Percentual da memória total do sistema (1-95) - **exclusivo com memory_mb**
- `duration_seconds`: Duração do teste em segundos (5-3600)
- `log_interval_sec`: Intervalo de log em segundos (1-60)

**Nota:** Forneça `memory_mb` OU `memory_percent`, não ambos.

### Verificar status

```bash
curl http://localhost:8080/status
```

### Obter logs

```bash
# Todos os logs
curl http://localhost:8080/logs

# Últimos 20 logs
curl http://localhost:8080/logs?limit=20
```

### Parar teste

```bash
curl -X POST http://localhost:8080/stop
```

### Limpar memória

```bash
curl -X POST http://localhost:8080/clear
```

### Health check

```bash
curl http://localhost:8080/health
```

## 🔬 Como Funciona

### Rotina 1: Construção da Árvore

A aplicação constrói uma árvore binária inserindo nós sequencialmente até atingir o consumo de memória alvo. Cada nó contém:
- Valor inteiro para organização
- Payload de dados (bytearray) para consumir memória
- Referências para filhos esquerdo e direito

### Rotina 2: Pesquisa na Árvore

Após construir a árvore, a aplicação realiza pesquisas aleatórias mantendo a memória alocada durante o período especificado. Isso simula carga de trabalho realista enquanto mantém o stress de memória.

## 📊 Exemplo de Log

```json
{
  "timestamp": "2025-10-03T14:30:45.123456",
  "operation": "BUILD_TREE_COMPLETE",
  "memory_use_mb": 512.45,
  "message": "Árvore construída com 5243 nós"
}
```

## 🧪 Exemplo de Teste Completo

### Usando Scripts Automatizados (MicroK8s)

```bash
# 1. Iniciar port-forward em um terminal
microk8s kubectl port-forward svc/memory-stress-service 8080:8080

# 2. Em outro terminal, executar testes
./test-stress.sh

# 3. Monitorar em tempo real
./monitor-stress.sh
```

### Teste Manual Completo

```bash
# 1. Iniciar teste com percentual de memória (50%)
curl -X POST http://localhost:8080/start \
  -H "Content-Type: application/json" \
  -d '{
    "memory_percent": 50,
    "duration_seconds": 300,
    "log_interval_sec": 15
  }'

# 2. Monitorar o status
watch -n 5 'curl -s http://localhost:8080/status | jq'

# 3. Verificar logs em tempo real
while true; do
  curl -s http://localhost:8080/logs?limit=5 | jq '.logs[-1]'
  sleep 5
done

# 4. Monitorar o pod no Kubernetes (MicroK8s)
microk8s kubectl top pod -l app=memory-stress-test --watch

# 5. Ver logs do pod
microk8s kubectl logs -l app=memory-stress-test -f

# 6. Após o teste, limpar memória
curl -X POST http://localhost:8080/clear
```

## 🐛 Troubleshooting

### Pod com OOMKilled

Se o pod for terminado com `OOMKilled`, aumente os limites de memória no deployment:

```yaml
resources:
  limits:
    memory: "4Gi"  # Ajuste conforme necessário
```

### Teste não atinge memória alvo

Verifique os logs para entender o comportamento. Ajuste o `payload_size_kb` no código se necessário.

### Aplicação não responde

Verifique os health checks:

```bash
kubectl describe pod -l app=memory-stress-test
kubectl logs -l app=memory-stress-test
```

## 📈 Monitoramento com Prometheus

A aplicação expõe métricas de memória que podem ser coletadas. Exemplo de query:

```promql
container_memory_usage_bytes{pod=~"memory-stress-test.*"}
```

## ⚠️ Avisos Importantes

- Use apenas em ambientes de teste/desenvolvimento
- Não execute em produção sem supervisão adequada
- Configure limites de recursos apropriados no Kubernetes
- Monitore o cluster para evitar impacto em outros pods
- O teste mantém a memória alocada até ser explicitamente limpa

## 📝 Estrutura do Projeto

```
.
├── stress_test.py              # Aplicação principal Python
├── requirements.txt            # Dependências Python
├── Dockerfile                  # Imagem Docker
├── kubernetes-deployment.yaml  # Manifesto K8s genérico
├── microk8s-deployment.yaml    # Manifesto otimizado para MicroK8s
│
├── setup-microk8s.sh          # Script de configuração do MicroK8s
├── deploy-microk8s.sh         # Script de deploy automático
├── test-stress.sh             # Script de testes automatizados
├── monitor-stress.sh          # Script de monitoramento em tempo real
├── cleanup.sh                 # Script de limpeza e remoção
│
├── README.md                   # Documentação principal (este arquivo)
├── QUICKSTART.md              # Guia de início rápido
├── EXAMPLES.md                # Exemplos práticos e casos de uso
└── ARCHITECTURE.md            # Documentação técnica da arquitetura
```

## 🛠️ Scripts Disponíveis

### setup-microk8s.sh
Instala e configura o MicroK8s com todos os addons necessários.

```bash
# Instalação inicial
sudo ./setup-microk8s.sh --install

# Configuração de addons
./setup-microk8s.sh
```

### deploy-microk8s.sh
Deploy automatizado completo: build, push e apply.

```bash
./deploy-microk8s.sh
```

### test-stress.sh
Executa uma bateria de testes na aplicação.

```bash
# Teste local (port-forward)
./test-stress.sh

# Teste via NodePort
./test-stress.sh http://NODE_IP:30080
```

### monitor-stress.sh
Monitora logs, métricas e status em tempo real.

```bash
# Monitor local
./monitor-stress.sh

# Monitor remoto
./monitor-stress.sh http://NODE_IP:30080 5
```

## 🤝 Contribuindo

Esta é uma ferramenta de pesquisa. Sugestões e melhorias são bem-vindas!

## 📖 Documentação Adicional

- **[QUICKSTART.md](QUICKSTART.md)** - Comece aqui! Guia de início rápido em 5 minutos
- **[EXAMPLES.md](EXAMPLES.md)** - Exemplos práticos e cenários de pesquisa
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detalhes técnicos da arquitetura

## 🎓 Casos de Uso

Esta ferramenta é ideal para:
- 📊 Pesquisas acadêmicas sobre gerenciamento de memória
- 🔬 Testes de escalabilidade de pods Kubernetes
- 📈 Análise de comportamento de OOMKill
- 🧪 Validação de limites de recursos
- 🎯 Benchmarking de infraestrutura
- 📉 Estudos de fragmentação de memória
- 🔍 Análise de performance de aplicações

## 💡 Features Principais

✅ **Controle Preciso**: Defina exatamente quanto de memória consumir  
✅ **Modo Percentual**: Adapta-se automaticamente ao ambiente  
✅ **Logs Detalhados**: Timestamp, operação e consumo em cada evento  
✅ **API REST**: Controle total via HTTP  
✅ **Thread Safe**: Suporte a requisições concorrentes  
✅ **Health Checks**: Integração nativa com Kubernetes  
✅ **Scripts Automatizados**: Deploy e testes com um comando  
✅ **Monitor em Tempo Real**: Visualize métricas enquanto testa  

## 🏆 Diferenciais

- **Árvore Binária**: Padrão realista de alocação de memória
- **Duas Rotinas**: Construção + Pesquisa para stress completo
- **MicroK8s Ready**: Scripts otimizados para ambiente local
- **Documentação Completa**: 4 arquivos de documentação detalhada
- **Zero Configuração**: Funciona out-of-the-box

---

**Desenvolvido para pesquisa em Kubernetes** | **Licença**: MIT | **Python 3.11+**