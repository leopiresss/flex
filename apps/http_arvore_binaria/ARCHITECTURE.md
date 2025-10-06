# 🏗️ Arquitetura da Solução

Este documento detalha a arquitetura técnica da aplicação de stress test de memória para Kubernetes.

## 📊 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Pod: memory-stress-test              │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │         Container: stress-app                     │  │ │
│  │  │  ┌────────────────────────────────────────────┐  │  │ │
│  │  │  │         Flask API (Port 8080)              │  │  │ │
│  │  │  │  ┌──────────────┐  ┌─────────────────┐    │  │  │ │
│  │  │  │  │  HTTP Routes │  │ StressTestManager│   │  │  │ │
│  │  │  │  └──────────────┘  └─────────────────┘    │  │  │ │
│  │  │  │           │                  │             │  │  │ │
│  │  │  │           └──────────────────┘             │  │  │ │
│  │  │  │                    │                       │  │  │ │
│  │  │  │         ┌──────────▼──────────┐           │  │  │ │
│  │  │  │         │   Binary Tree       │           │  │  │ │
│  │  │  │         │   (Memory Consumer) │           │  │  │ │
│  │  │  │         └─────────────────────┘           │  │  │ │
│  │  │  └────────────────────────────────────────────┘  │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌───────────────────────────▼───────────────────────────┐  │
│  │        Service: memory-stress-service (NodePort)      │  │
│  │                    Port: 8080/30080                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   External Access   │
                    │  (curl, browser)    │
                    └─────────────────────┘
```

## 🧩 Componentes Principais

### 1. TreeNode (Nó da Árvore Binária)

Estrutura de dados fundamental que consome memória:

```python
class TreeNode:
    - value: int           # Valor para ordenação
    - left: TreeNode       # Referência ao filho esquerdo
    - right: TreeNode      # Referência ao filho direito
    - data: bytearray      # Payload de memória (100 KB padrão)
```

**Características:**
- Cada nó aloca um bytearray de tamanho configurável
- Estrutura balanceada automaticamente por inserções aleatórias
- Operações de inserção e busca em O(log n) em média

### 2. StressTestManager

Gerenciador central de testes:

```python
class StressTestManager:
    - root: TreeNode           # Raiz da árvore
    - logs: List[LogEntry]     # Histórico de logs
    - is_running: bool         # Estado do teste
    - stop_flag: bool          # Flag de parada
    - lock: threading.Lock     # Sincronização de threads
    - config: dict             # Configuração atual
    - process: psutil.Process  # Monitoramento de memória
```

**Responsabilidades:**
- Gerenciar ciclo de vida dos testes
- Coordenar rotinas de stress
- Coletar e armazenar logs
- Monitorar uso de memória

### 3. Flask API

Interface HTTP RESTful:

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações da API |
| `/start` | POST | Inicia teste de stress |
| `/stop` | POST | Para teste em execução |
| `/status` | GET | Status atual |
| `/logs` | GET | Retorna logs |
| `/clear` | POST | Limpa memória |
| `/health` | GET | Health check |

## 🔄 Fluxo de Execução

### Fase 1: Inicialização do Teste

```
1. Usuário → POST /start com parâmetros
   ↓
2. Flask valida parâmetros
   ↓
3. Calcula memória alvo (se memory_percent fornecido)
   ↓
4. Cria thread para execução assíncrona
   ↓
5. Retorna confirmação imediata ao usuário
```

### Fase 2: Construção da Árvore (build_tree_routine)

```
1. Inicializa árvore com nó raiz
   ↓
2. Loop de inserção:
   │
   ├─→ Gera valores aleatórios
   │
   ├─→ Insere nós na árvore
   │
   ├─→ Verifica memória atual
   │
   ├─→ Compara com memória alvo
   │
   └─→ Continua até atingir alvo ou stop_flag
   ↓
3. Loga conclusão da construção
```

### Fase 3: Pesquisa na Árvore (search_tree_routine)

```
1. Inicia contador de pesquisas
   ↓
2. Loop de busca:
   │
   ├─→ Gera valores aleatórios
   │
   ├─→ Busca valores na árvore
   │
   ├─→ Verifica tempo decorrido
   │
   ├─→ Loga status periodicamente
   │
   └─→ Continua até duração ou stop_flag
   ↓
3. Finaliza e mantém árvore na memória
```

### Fase 4: Monitoramento Contínuo

```
Durante toda execução:
   │
   ├─→ psutil.Process().memory_info().rss
   │   (Coleta uso de memória RSS)
   │
   ├─→ Timestamp de cada operação
   │
   ├─→ Armazena em logs thread-safe
   │
   └─→ Disponibiliza via /status e /logs
```

## 🎯 Algoritmo da Árvore Binária

### Por que Árvore Binária?

1. **Padrão de alocação realista**: Simula alocação de memória em aplicações reais
2. **Fragmentação controlada**: Nós espalhados na memória (não contíguo)
3. **Operações ativas**: Manter CPU ocupada com buscas
4. **Escalabilidade**: Cresce logaritmicamente em profundidade
5. **Previsibilidade**: Tamanho de cada nó é conhecido

### Inserção (O(log n) em média)

```python
def insert(self, value, payload_size_kb):
    if value < self.value:
        if self.left is None:
            self.left = TreeNode(value, payload_size_kb)
        else:
            self.left.insert(value, payload_size_kb)
    else:
        if self.right is None:
            self.right = TreeNode(value, payload_size_kb)
        else:
            self.right.insert(value, payload_size_kb)
```

### Busca (O(log n) em média)

```python
def search(self, value):
    if value == self.value:
        return True
    elif value < self.value and self.left:
        return self.left.search(value)
    elif value > self.value and self.right:
        return self.right.search(value)
    return False
```

### Cálculo de Memória

```
Memória por nó = sizeof(TreeNode) + payload_size

TreeNode overhead ≈ 48 bytes (Python object)
  - value: 28 bytes (int)
  - left: 8 bytes (pointer)
  - right: 8 bytes (pointer)
  - data: 8 bytes (pointer to bytearray)

Payload padrão = 100 KB

Total por nó ≈ 100 KB + 48 bytes ≈ 100 KB
```

Para atingir X MB:
```
Número de nós ≈ (X * 1024) / 100
```

## 🔒 Thread Safety

### Recursos Compartilhados

- `logs`: Protegido por `lock` durante append
- `root`: Substituído atomicamente (nova instância)
- `is_running`: Acesso atômico (boolean)
- `config`: Substituído atomicamente (dict)

### Padrão de Sincronização

```python
with self.lock:
    # Operações em recursos compartilhados
    self.logs.append(log_entry)
```

## 📦 Containerização

### Dockerfile Layers

```
1. Base Image: python:3.11-slim
   ↓
2. System Dependencies: gcc (para psutil)
   ↓
3. Python Dependencies: Flask, psutil, Werkzeug
   ↓
4. Application Code: stress_test.py
   ↓
5. Expose Port: 8080
   ↓
6. CMD: python stress_test.py
```

### Resource Requests/Limits

```yaml
resources:
  requests:
    memory: "128Mi"  # Mínimo para iniciar
    cpu: "100m"      # 0.1 CPU core
  limits:
    memory: "2Gi"    # Máximo permitido (OOMKill acima)
    cpu: "1000m"     # 1 CPU core
```

## 🔍 Monitoramento de Memória

### psutil.Process()

```python
process = psutil.Process(os.getpid())
memory_info = process.memory_info()

# RSS (Resident Set Size)
rss_bytes = memory_info.rss
rss_mb = rss_bytes / (1024 * 1024)
```

### Métricas Coletadas

1. **RSS (Resident Set Size)**: Memória física usada
2. **Timestamp**: Momento da coleta
3. **Operação**: Contexto da medição
4. **Percentual**: Relativo à memória total do sistema

## 🌐 API Design

### REST Principles

- **Stateless**: Cada requisição é independente
- **Resource-based**: URLs representam recursos
- **HTTP Methods**: POST para ações, GET para consultas
- **JSON**: Formato padrão de dados

### Error Handling

```python
# Validação de parâmetros
if memory_mb < 10 or memory_mb > 10000:
    return jsonify({'error': 'message'}), 400

# Thread safety
try:
    with self.lock:
        # operação
except Exception as e:
    self.add_log("ERROR", str(e))
```

## 🚀 Performance

### Otimizações

1. **Inserções em lote**: 10 nós por iteração
2. **Sleeps estratégicos**: Evitar 100% CPU
3. **Buscas em lote**: 100 buscas por iteração
4. **Logs controlados**: Apenas em intervalos configurados

### Gargalos Potenciais

1. **Criação de nós**: Alocação de bytearray é custosa
2. **Percurso da árvore**: Profundidade cresce com nós
3. **GC (Garbage Collector)**: Pode pausar durante limpeza
4. **Fragmentação**: Memória pode ficar fragmentada

## 🔧 Configurabilidade

### Parâmetros Ajustáveis

| Parâmetro | Faixa | Impacto |
|-----------|-------|---------|
| memory_mb | 10-10000 | Tamanho da árvore |
| memory_percent | 1-95 | Adaptável ao ambiente |
| duration_seconds | 5-3600 | Tempo de stress |
| log_interval_sec | 1-60 | Frequência de logs |
| payload_size_kb | Código | Memória por nó |

### Hard-coded Constants

```python
payload_size_kb = 100  # Tamanho do payload por nó
insert_batch_size = 10  # Nós por lote
search_batch_size = 100  # Buscas por lote
build_sleep = 0.01  # Pausa durante construção (10ms)
search_sleep = 0.05  # Pausa durante busca (50ms)
```

## 🎛️ Kubernetes Integration

### Health Checks

#### Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 30
```
**Objetivo**: Detectar se o container está travado

#### Readiness Probe
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```
**Objetivo**: Verificar se está pronto para receber tráfego

### Service Discovery

```yaml
Service (NodePort):
  - ClusterIP: Acesso interno
  - NodePort: 30080 (acesso externo)
  - Port: 8080 (porta do service)
  - TargetPort: 8080 (porta do container)
```

### Image Registry

**MicroK8s Registry Local:**
```
localhost:32000/memory-stress-test:latest
```

**Vantagens:**
- Não precisa de registry externo
- Deploy rápido (local)
- Ideal para desenvolvimento

## 🔐 Segurança

### Considerações

1. **Sem autenticação**: API aberta (OK para ambiente de teste)
2. **Limites de recursos**: Proteção contra OOMKill
3. **Validação de entrada**: Previne valores inválidos
4. **Sem persistência**: Dados apenas em memória

### Melhorias Sugeridas (Produção)

```python
# Adicionar autenticação
from flask_httpauth import HTTPBasicAuth

# Rate limiting
from flask_limiter import Limiter

# HTTPS
# Usar certificados TLS

# RBAC no Kubernetes
# ServiceAccount com permissões limitadas
```

## 📊 Logs e Observabilidade

### Estrutura de Log

```json
{
  "timestamp": "2025-10-03T14:30:45.123456",
  "operation": "BUILD_TREE_COMPLETE",
  "memory_use_mb": 512.45,
  "message": "Árvore construída com 5243 nós"
}
```

### Operações Logadas

| Operação | Momento | Dados |
|----------|---------|-------|
| STRESS_TEST_START | Início do teste | Configuração |
| BUILD_TREE_START | Início construção | Memória alvo |
| BUILD_TREE_TARGET | Alvo atingido | Número de nós |
| BUILD_TREE_COMPLETE | Construção completa | Total de nós |
| SEARCH_TREE_START | Início buscas | Duração esperada |
| SEARCH_TREE_PROGRESS | Durante buscas | Progresso |
| SEARCH_TREE_COMPLETE | Fim buscas | Total de buscas |
| STRESS_TEST_COMPLETE | Fim do teste | Sucesso |
| STRESS_TEST_STOPPED | Interrompido | Manual |
| STRESS_TEST_ERROR | Erro | Mensagem de erro |
| MEMORY_CLEARED | Limpeza | Memória liberada |

### Integração com Ferramentas

**Prometheus (futuro):**
```python
from prometheus_client import Counter, Gauge

memory_usage = Gauge('stress_memory_mb', 'Memory usage in MB')
tests_total = Counter('stress_tests_total', 'Total stress tests')
```

**ELK Stack (futuro):**
```python
import logging
logging.config.dictConfig({
    'handlers': {
        'logstash': {
            'class': 'logstash.TCPLogstashHandler',
            'host': 'logstash-service',
            'port': 5000
        }
    }
})
```

## 🧪 Casos de Uso da Árvore Binária

### 1. Stress de Memória

**Objetivo**: Preencher memória de forma controlada

**Vantagem da árvore**:
- Alocação não-contígua (fragmentação realista)
- Overhead de ponteiros (simula objetos complexos)
- Crescimento previsível

### 2. Stress de CPU (Buscas)

**Objetivo**: Manter CPU ativa durante o teste

**Vantagem da árvore**:
- Operação O(log n) - trabalho real
- Cache thrashing (nós espalhados na memória)
- Padrão de acesso imprevisível

### 3. Pesquisa de Limites

**Objetivo**: Encontrar limite de OOMKill

**Vantagem da árvore**:
- Crescimento incremental
- Fácil de medir (nós × tamanho)
- Reproduzível

### 4. Análise de GC

**Objetivo**: Estudar comportamento do Garbage Collector

**Vantagem da árvore**:
- Muitas referências circulares
- Objetos de tamanhos variados
- Padrão de alocação complexo

## 🔄 Ciclo de Vida Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INIT                                                      │
│    - Flask app inicia                                        │
│    - StressTestManager criado                                │
│    - Estado inicial: is_running=False                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. READY                                                     │
│    - Aguardando requisições                                  │
│    - Health checks respondendo                               │
│    - /status retorna estado inicial                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ POST /start
┌─────────────────────────────────────────────────────────────┐
│ 3. BUILDING                                                  │
│    - is_running=True                                         │
│    - Thread de stress iniciada                               │
│    - Construindo árvore binária                              │
│    - Logs: BUILD_TREE_*                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ Memória alvo atingida
┌─────────────────────────────────────────────────────────────┐
│ 4. SEARCHING                                                 │
│    - Árvore construída                                       │
│    - Executando buscas                                       │
│    - Mantendo memória alocada                                │
│    - Logs: SEARCH_TREE_*                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ Duração completa OU POST /stop
┌─────────────────────────────────────────────────────────────┐
│ 5. COMPLETED                                                 │
│    - Thread finalizada                                       │
│    - is_running=False                                        │
│    - Árvore ainda na memória                                 │
│    - Logs: STRESS_TEST_COMPLETE                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ POST /clear
┌─────────────────────────────────────────────────────────────┐
│ 6. CLEANED                                                   │
│    - Árvore destruída (root=None)                            │
│    - GC libera memória                                       │
│    - Pronto para novo teste                                  │
│    - Logs: MEMORY_CLEARED                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     └──────────► Volta para READY
```

## 💾 Consumo de Memória Detalhado

### Breakdown de Memória

```
Total Memory = Base + Tree + Overhead

Base (Python + Flask):
  - Python interpreter: ~10-20 MB
  - Flask framework: ~5-10 MB
  - psutil library: ~2-5 MB
  - Outros imports: ~5 MB
  Total Base: ~25-40 MB

Tree Memory:
  - Cada nó: ~100 KB (payload) + 48 bytes (objeto)
  - Para 1024 MB alvo: ~10,240 nós
  - Total Tree: ~1024 MB

Overhead:
  - Logs (JSON): ~100 KB - 1 MB
  - Threads: ~1-2 MB
  - Sistema: ~5-10 MB
  Total Overhead: ~6-13 MB

Memória Total Esperada:
  Alvo 1024 MB → RSS ~1090-1100 MB
```

### Crescimento de Memória

```
Tempo (s) │ Fase          │ Memória (MB) │ Nós
──────────┼───────────────┼──────────────┼──────────
0         │ Init          │ 35           │ 0
5         │ Building      │ 256          │ 2,560
10        │ Building      │ 512          │ 5,120
15        │ Building      │ 768          │ 7,680
20        │ Built         │ 1024         │ 10,240
25        │ Searching     │ 1024         │ 10,240
...       │ Searching     │ 1024         │ 10,240
120       │ Complete      │ 1024         │ 10,240
125       │ Cleared       │ 40           │ 0
```

## 🎯 Design Decisions

### Por que Flask?

✅ Leve e simples
✅ Ideal para APIs REST
✅ Boa documentação
✅ Fácil de testar
❌ Não async por padrão (OK para este caso)

### Por que Threading?

✅ Simples de implementar
✅ Suficiente para um worker
✅ GIL não é problema (I/O bound nas APIs)
❌ Não escala para múltiplos workers

### Por que Árvore Binária?

✅ Padrão realista de alocação
✅ Operações ativas (buscas)
✅ Previsível e controlável
✅ Fragmentação de memória
❌ Mais complexo que lista/array

### Por que psutil?

✅ Multiplataforma
✅ Métricas confiáveis
✅ API simples
✅ Bem mantido
❌ Dependência extra

## 🔮 Extensões Futuras

### 1. Múltiplos Padrões de Stress

```python
class StressPattern(Enum):
    BINARY_TREE = "binary_tree"
    LINKED_LIST = "linked_list"
    HASH_TABLE = "hash_table"
    MATRIX = "matrix"
```

### 2. Métricas Avançadas

```python
- CPU usage tracking
- I/O statistics
- Network metrics
- Cache hit rates
```

### 3. WebSocket para Logs Real-time

```python
from flask_socketio import SocketIO

socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    emit('logs', stream_logs())
```

### 4. Persistência de Resultados

```python
import sqlite3

# Salvar histórico de testes
# Comparar resultados
# Análise temporal
```

### 5. Horizontal Scaling

```yaml
replicas: 3  # Múltiplos pods
# Comparar stress entre pods
# Load balancing
```

## 📚 Referências Técnicas

### Estruturas de Dados
- Binary Search Tree: O(log n) ops
- Balanced Tree: AVL, Red-Black (futuro)

### Python Memory Management
- CPython Reference Counting
- Generational Garbage Collection
- Memory Pools

### Kubernetes Resources
- Requests vs Limits
- OOMKill behavior
- QoS Classes

### Container Memory
- RSS vs Cache
- cgroups memory.limit_in_bytes
- oom_score_adj

---

**Versão**: 1.0  
**Última atualização**: 2025-10-03  
**Autor**: Sistema de Stress Test para Kubernetes