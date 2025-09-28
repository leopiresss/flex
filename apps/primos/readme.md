# 🚀 Servidor de Teste de Stress - Gerador de Números Primos

Este projeto implementa um servidor HTTP em Python para testes de stress que gera números primos sob demanda e registra métricas detalhadas de performance.

## 📋 Características

- **Servidor HTTP**: Recebe requisições para gerar números primos
- **Logging Automático**: Registra todas as execuções em arquivo CSV
- **API RESTful**: Endpoints bem definidos com respostas JSON
- **Thread-Safe**: Suporta múltiplas requisições simultâneas
- **Cliente de Teste**: Script completo para testes de stress
- **Métricas Detalhadas**: Timestamps, duração e contadores

## 📦 Instalação

1. **Clone o projeto** (ou copie os arquivos)

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

## 🏃‍♂️ Como Usar

### 1. Iniciar o Servidor

```bash
python prime_server.py
```

O servidor será iniciado em `http://localhost:5000`

### 2. Fazer Requisições

#### Via Query String:
```bash
curl "http://localhost:5000/primes?count=100"
```

#### Via Parâmetro na URL:
```bash
curl "http://localhost:5000/primes/100"
```

#### Exemplo de Resposta:
```json
{
  "qtd_numeros_primos": 100,
  "lista_numeros_primos": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, ...],
  "duracao_execucao_ms": 45,
  "timestamp_execucao": 1696435200000
}
```

### 3. Executar Testes de Stress

```bash
python prime_test_client.py
```

O cliente oferece várias opções:
- Teste simples
- Teste personalizado
- Testes progressivos
- Verificação de logs

## 🔗 Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/primes?count=N` | GET | Gera N números primos (via query) |
| `/primes/N` | GET | Gera N números primos (via URL) |
| `/health` | GET | Verificação de saúde do servidor |
| `/logs` | GET | Visualiza últimos logs gerados |
| `/` | GET | Página de ajuda com documentação |

## 📊 Sistema de Logging

O servidor grava automaticamente um arquivo `prime_server_log.csv` com:

| Campo | Descrição |
|-------|-----------|
| `timestamp_inicio` | Timestamp de início da execução (ms) |
| `timestamp_fim` | Timestamp de fim da execução (ms) |
| `duracao_ms` | Duração total da execução (ms) |
| `qtd_primos_gerados` | Quantidade de números primos gerados |

### Exemplo do CSV:
```csv
timestamp_inicio,timestamp_fim,duracao_ms,qtd_primos_gerados
1696435200123,1696435200168,45,100
1696435201234,1696435201456,222,500
```

## 🧪 Exemplos de Teste de Stress

### Teste Simples com curl:
```bash
# Gera 10 números primos
curl "http://localhost:5000/primes?count=10"

# Gera 1000 números primos
curl "http://localhost:5000/primes/1000"
```

### Teste com múltiplas requisições simultâneas:
```bash
# Usando o cliente Python
python prime_test_client.py
# Escolha opção 2 para teste personalizado
```

### Teste de stress com ab (Apache Bench):
```bash
# 100 requisições, 10 simultâneas
ab -n 100 -c 10 "http://localhost:5000/primes?count=100"
```

### Teste com hey:
```bash
# 1000 requisições, 50 workers
hey -n 1000 -c 50 "http://localhost:5000/primes?count=200"
```

## ⚡ Performance

- **Algoritmo Otimizado**: Usa teste de primalidade eficiente
- **Limite de Segurança**: Máximo de 10.000 números primos por requisição
- **Thread-Safe**: Suporta requisições simultâneas
- **Logging Assíncrono**: Não impacta performance das requisições

## 🔧 Configuração

### Alterar Porta:
Edite o arquivo `prime_server.py` na última linha:
```python
app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
```

### Alterar Limite Máximo:
Modifique a validação nos endpoints:
```python
if count > 20000:  # Novo limite
    return jsonify({'error': 'Limite máximo de 20.000'}), 400
```

## 📈 Monitoramento

### Verificar Saúde do Servidor:
```bash
curl http://localhost:5000/health
```

### Visualizar Logs:
```bash
curl http://localhost:5000/logs
```

### Monitorar Arquivo de Log:
```bash
tail -f prime_server_log.csv
```

## 🐛 Troubleshooting

### Servidor não inicia:
- Verifique se a porta 5000 está disponível
- Confirme se as dependências estão instaladas
- Execute `python --version` (requer Python 3.6+)

### Requisições lentas:
- Reduza o número de primos solicitados
- Verifique recursos do sistema (CPU/RAM)
- Monitore o arquivo de log para identificar gargalos

### Erro "Connection refused":
- Confirme se o servidor está rodando
- Verifique se está usando a URL correta
- Teste o endpoint `/health`

## 🎯 Casos de Uso

1. **Teste de Carga**: Avaliar performance sob diferentes cargas
2. **Benchmark**: Comparar performance entre diferentes sistemas
3. **Stress Test**: Identificar limites e pontos de falha
4. **Monitoramento**: Acompanhar métricas de performance ao longo do tempo
5. **Desenvolvimento**: Testar otimizações de algoritmo

## 📝 Estrutura de Arquivos

```
projeto/
├── prime_server.py          # Servidor principal
├── prime_test_client.py     # Cliente de teste
├── requirements.txt         # Dependências
├── README.md               # Este arquivo
└── prime_server_log.csv    # Log gerado automaticamente
```

## 🤝 Contribuição

Sugestões de melhorias:
- Implementação de cache para números primos
- Suporte a diferentes algoritmos de geração
- Interface web para monitoramento
- Exportação de métricas para Prometheus
- Dockerização do projeto

---

**🔥 Pronto para testar a performance do seu sistema!**