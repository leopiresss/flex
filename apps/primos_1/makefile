# Makefile para automação do deploy do Servidor de Números Primos
# Uso: make deploy, make clean, make test, etc.

# Variáveis
APP_NAME = prime-server
IMAGE_NAME = prime-server:latest
NAMESPACE = default
SERVICE_NAME = prime-server-service
DEPLOYMENT_NAME = prime-server
MANIFEST_FILE = prime-server-k8s.yaml
NODEPORT = 30071
LOGS_DIR = /logs

# Cores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m

.PHONY: help deploy clean build test status logs restart scale check-deps

# Target padrão
all: deploy

# Ajuda
help:
	@echo "$(GREEN)Makefile para Deploy do Servidor de Números Primos$(NC)"
	@echo ""
	@echo "$(YELLOW)Comandos disponíveis:$(NC)"
	@echo "  make deploy      - Deploy completo da aplicação"
	@echo "  make build       - Apenas construir e importar imagem"
	@echo "  make clean       - Remover aplicação do cluster"
	@echo "  make test        - Testar aplicação"
	@echo "  make status      - Ver status dos pods e serviços"
	@echo "  make logs        - Ver logs da aplicação (Kubernetes)"
	@echo "  make logs-local     - Ver logs persistentes locais"
	@echo "  make logs-local-follow - Seguir logs locais em tempo real"
	@echo "  make restart     - Reiniciar aplicação"
	@echo "  make scale n=X   - Escalar para X réplicas"
	@echo "  make check-deps  - Verificar dependências"
	@echo ""

# Verificar dependências
check-deps:
	@echo "$(YELLOW)Verificando dependências...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Docker não instalado!$(NC)"; exit 1; }
	@command -v microk8s >/dev/null 2>&1 || { echo "$(RED)MicroK8s não instalado!$(NC)"; exit 1; }
	@microk8s status --wait-ready --timeout=10 >/dev/null 2>&1 || { echo "$(RED)MicroK8s não está funcionando!$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Todas as dependências estão OK$(NC)"

# Criar diretório de logs
setup-logs:
	@echo "$(YELLOW)Criando diretório de logs...$(NC)"
	@sudo mkdir -p $(LOGS_DIR)
	@sudo chmod 777 $(LOGS_DIR)
	@sudo touch $(LOGS_DIR)/prime_server_log.csv
	@sudo chmod 666 $(LOGS_DIR)/prime_server_log.csv
	@echo "$(GREEN)✓ Diretório de logs criado: $(LOGS_DIR)$(NC)"

# Construir imagem
build: check-deps setup-logs
	@echo "$(YELLOW)Construindo imagem Docker...$(NC)"
	docker build -t $(IMAGE_NAME) .
	@echo "$(YELLOW)Exportando imagem...$(NC)"
	docker save $(IMAGE_NAME) > prime-server.tar
	@echo "$(YELLOW)Importando no MicroK8s...$(NC)"
	microk8s ctr image import prime-server.tar
	@rm -f prime-server.tar
	@echo "$(GREEN)✓ Imagem construída e importada$(NC)"

# Deploy completo
deploy: build
	@echo "$(YELLOW)Iniciando deploy...$(NC)"
	@echo "$(YELLOW)Removendo deployment anterior (se existir)...$(NC)"
	-microk8s kubectl delete -f $(MANIFEST_FILE) --ignore-not-found=true
	@sleep 5
	@echo "$(YELLOW)Aplicando manifesto...$(NC)"
	microk8s kubectl apply -f $(MANIFEST_FILE)
	@echo "$(YELLOW)Aguardando pods ficarem prontos...$(NC)"
	microk8s kubectl wait --for=condition=ready pod -l app=$(APP_NAME) --timeout=120s
	@echo "$(GREEN)✓ Deploy concluído com sucesso!$(NC)"
	@make status
	@make test

# Testar aplicação
test:
	@echo "$(YELLOW)Testando aplicação...$(NC)"
	@sleep 10
	@if curl -s --max-time 10 http://localhost:$(NODEPORT)/health > /dev/null; then \
		echo "$(GREEN)✓ Aplicação está respondendo!$(NC)"; \
		echo "$(YELLOW)Resultado do health check:$(NC)"; \
		curl -s http://localhost:$(NODEPORT)/health | python3 -m json.tool; \
	else \
		echo "$(RED)✗ Aplicação não está respondendo$(NC)"; \
		echo "$(YELLOW)Verifique os logs: make logs$(NC)"; \
	fi

# Ver status
status:
	@echo "$(YELLOW)Status dos Pods:$(NC)"
	@microk8s kubectl get pods -l app=$(APP_NAME)
	@echo ""
	@echo "$(YELLOW)Status dos Serviços:$(NC)"
	@microk8s kubectl get svc $(SERVICE_NAME)
	@echo ""
	@echo "$(YELLOW)URLs de acesso:$(NC)"
	@echo "  Health: http://localhost:$(NODEPORT)/health"
	@echo "  Primos: http://localhost:$(NODEPORT)/primes?count=10"
	@echo "  Logs:   http://localhost:$(NODEPORT)/logs"
	@echo ""
	@echo "$(YELLOW)Logs persistentes:$(NC)"
	@echo "  Diretório: $(LOGS_DIR)/"
	@echo "  Arquivo:   $(LOGS_DIR)/prime_server_log.csv"
	@echo "  Ver logs:  tail -f $(LOGS_DIR)/prime_server_log.csv"

# Ver logs
logs:
	@echo "$(YELLOW)Logs da aplicação:$(NC)"
	microk8s kubectl logs -l app=$(APP_NAME) --tail=50

# Ver logs locais persistentes
logs-local:
	@echo "$(YELLOW)Logs persistentes do arquivo local:$(NC)"
	@if [ -f "$(LOGS_DIR)/prime_server_log.csv" ]; then \
		tail -20 $(LOGS_DIR)/prime_server_log.csv; \
	else \
		echo "$(RED)Arquivo de log não encontrado: $(LOGS_DIR)/prime_server_log.csv$(NC)"; \
	fi

# Seguir logs locais em tempo real
logs-local-follow:
	@echo "$(YELLOW)Seguindo logs locais em tempo real (Ctrl+C para sair):$(NC)"
	@tail -f $(LOGS_DIR)/prime_server_log.csv
# Seguir logs em tempo real
logs-follow:
	@echo "$(YELLOW)Seguindo logs em tempo real (Ctrl+C para sair):$(NC)"
	microk8s kubectl logs -f -l app=$(APP_NAME)

# Limpar/remover aplicação
clean:
	@echo "$(YELLOW)Removendo aplicação...$(NC)"
	microk8s kubectl delete -f $(MANIFEST_FILE)
	@echo "$(GREEN)✓ Aplicação removida$(NC)"

# Reiniciar aplicação
restart:
	@echo "$(YELLOW)Reiniciando aplicação...$(NC)"
	microk8s kubectl rollout restart deployment/$(DEPLOYMENT_NAME)
	microk8s kubectl wait --for=condition=ready pod -l app=$(APP_NAME) --timeout=120s
	@echo "$(GREEN)✓ Aplicação reiniciada$(NC)"

# Escalar aplicação
scale:
	@if [ -z "$(n)" ]; then \
		echo "$(RED)Uso: make scale n=X (onde X é o número de réplicas)$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Escalando para $(n) réplicas...$(NC)"
	microk8s kubectl scale deployment $(DEPLOYMENT_NAME) --replicas=$(n)
	microk8s kubectl wait --for=condition=ready pod -l app=$(APP_NAME) --timeout=120s
	@echo "$(GREEN)✓ Escalado para $(n) réplicas$(NC)"
	@make status

# Acessar pod (shell)
shell:
	@echo "$(YELLOW)Acessando shell do primeiro pod...$(NC)"
	@POD_NAME=$$(microk8s kubectl get pods -l app=$(APP_NAME) -o jsonpath='{.items[0].metadata.name}'); \
	microk8s kubectl exec -it $$POD_NAME -- bash

# Debug - informações detalhadas
debug:
	@echo "$(YELLOW)=== INFORMAÇÕES DE DEBUG ===$(NC)"
	@echo "$(YELLOW)Pods:$(NC)"
	@microk8s kubectl get pods -l app=$(APP_NAME) -o wide
	@echo ""
	@echo "$(YELLOW)Describe Pods:$(NC)"
	@microk8s kubectl describe pods -l app=$(APP_NAME)
	@echo ""
	@echo "$(YELLOW)Serviços:$(NC)"
	@microk8s kubectl get svc $(SERVICE_NAME) -o wide
	@echo ""
	@echo "$(YELLOW)Endpoints:$(NC)"
	@microk8s kubectl get endpoints $(SERVICE_NAME)
	@echo ""
	@echo "$(YELLOW)Eventos:$(NC)"
	@microk8s kubectl get events --sort-by=.metadata.creationTimestamp | tail -20

# Deploy com auto-scaling
deploy-with-hpa: deploy
	@echo "$(YELLOW)Aplicando auto-scaling...$(NC)"
	microk8s kubectl apply -f deploy-automation.yaml
	@echo "$(GREEN)✓ Auto-scaling configurado$(NC)"

# Monitoramento contínuo
monitor:
	@echo "$(YELLOW)Monitoramento contínuo (Ctrl+C para sair):$(NC)"
	@while true; do \
		clear; \
		echo "$(GREEN)=== MONITORAMENTO SERVIDOR PRIMOS ====$(NC)"; \
		echo "$(YELLOW)Timestamp: $$(date)$(NC)"; \
		echo ""; \
		make status 2>/dev/null || true; \
		echo ""; \
		echo "$(YELLOW)Testando conectividade:$(NC)"; \
		if curl -s --max-time 3 http://localhost:$(NODEPORT)/health >/dev/null 2>&1; then \
			echo "$(GREEN)✓ Aplicação OK$(NC)"; \
		else \
			echo "$(RED)✗ Aplicação com problemas$(NC)"; \
		fi; \
		sleep 5; \
	done