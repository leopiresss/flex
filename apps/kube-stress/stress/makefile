# Makefile para Memory Stress Test no Kubernetes/MicroK8s
# Uso: make [comando]

# Variáveis
KUBECTL := microk8s kubectl
HELM := microk8s helm3
DOCKER := docker
NAMESPACE := memory-stress-test
APP_NAME := memory-stress-app
IMAGE_NAME := memory-stress:latest
REGISTRY_IMAGE := localhost:32000/memory-stress:latest
DEPLOYMENT_FILE := simple_stress_deployment.yaml

# Cores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help
help: ## Mostra esta ajuda detalhada
	@echo ""
	@echo "$(BLUE)============================================================================"
	@echo "                    Memory Stress Test - Makefile"
	@echo "============================================================================$(NC)"
	@echo ""
	@echo "$(GREEN)DESCRIÇÃO:$(NC)"
	@echo "  Makefile para gerenciar aplicação de teste de stress de memória"
	@echo "  usando árvore binária em ambiente Kubernetes/MicroK8s."
	@echo ""
	@echo "$(GREEN)USO:$(NC)"
	@echo "  make [comando] [VARIÁVEL=valor]"
	@echo ""
	@echo "$(GREEN)COMANDOS PRINCIPAIS:$(NC)"
	@echo ""
	@echo "  $(YELLOW)📦 INSTALAÇÃO E DEPLOY$(NC)"
	@echo "  $(BLUE)make install$(NC)              Instalação completa (recomendado para primeira vez)"
	@echo "  $(BLUE)make setup$(NC)                Configura ambiente (addons, kubeconfig)"
	@echo "  $(BLUE)make build$(NC)                Build da imagem Docker local"
	@echo "  $(BLUE)make import$(NC)               Importa imagem para MicroK8s"
	@echo "  $(BLUE)make deploy$(NC)               Deploy da aplicação no Kubernetes"
	@echo ""
	@echo "  $(YELLOW)🗑️  DESINSTALAÇÃO$(NC)"
	@echo "  $(BLUE)make uninstall$(NC)            Remove aplicação do Kubernetes"
	@echo "  $(BLUE)make clean$(NC)                Remove aplicação + imagens Docker"
	@echo ""
	@echo "  $(YELLOW)📊 MONITORAMENTO$(NC)"
	@echo "  $(BLUE)make status$(NC)               Mostra status geral (pods, deployments, etc)"
	@echo "  $(BLUE)make logs$(NC)                 Logs em tempo real (Ctrl+C para sair)"
	@echo "  $(BLUE)make logs-tail$(NC)            Últimas 100 linhas dos logs"
	@echo "  $(BLUE)make top$(NC)                  Uso de CPU e Memória dos pods"
	@echo "  $(BLUE)make watch$(NC)                Monitora pods continuamente"
	@echo "  $(BLUE)make events$(NC)               Eventos do namespace"
	@echo "  $(BLUE)make describe$(NC)             Detalhes completos dos pods"
	@echo ""
	@echo "  $(YELLOW)⚙️  GERENCIAMENTO$(NC)"
	@echo "  $(BLUE)make restart$(NC)              Reinicia a aplicação"
	@echo "  $(BLUE)make shell$(NC)                Abre shell dentro do pod"
	@echo "  $(BLUE)make scale REPLICAS=N$(NC)     Escala aplicação (ex: make scale REPLICAS=3)"
	@echo ""
	@echo "  $(YELLOW)🔧 CONFIGURAÇÃO$(NC)"
	@echo "  $(BLUE)make config-memory MB=N$(NC)   Define memória target em MB"
	@echo "                             Exemplo: make config-memory MB=800"
	@echo "  $(BLUE)make config-duration SEC=N$(NC) Define duração em segundos"
	@echo "                             Exemplo: make config-duration SEC=1800"
	@echo ""
	@echo "  $(YELLOW)🧪 TESTES PRÉ-CONFIGURADOS$(NC)"
	@echo "  $(BLUE)make test-basic$(NC)           Teste básico: 500MB por 10 minutos"
	@echo "  $(BLUE)make test-intense$(NC)         Teste intensivo: 800MB por 30 minutos"
	@echo "  $(BLUE)make test-oom$(NC)             Teste OOMKill: força limite (1500MB)"
	@echo ""
	@echo "  $(YELLOW)🛠️  DESENVOLVIMENTO$(NC)"
	@echo "  $(BLUE)make dev$(NC)                  Build + Import + Restart + Logs"
	@echo "  $(BLUE)make info$(NC)                 Informações do sistema"
	@echo "  $(BLUE)make check-microk8s$(NC)       Verifica se MicroK8s está OK"
	@echo ""
	@echo "$(GREEN)VARIÁVEIS DISPONÍVEIS:$(NC)"
	@echo "  REPLICAS     Número de réplicas (padrão: 1)"
	@echo "  MB           Memória target em MB (padrão: 500)"
	@echo "  SEC          Duração em segundos (padrão: 3600)"
	@echo ""
	@echo "$(GREEN)EXEMPLOS DE USO:$(NC)"
	@echo ""
	@echo "  $(YELLOW)# Instalação inicial$(NC)"
	@echo "  make install"
	@echo ""
	@echo "  $(YELLOW)# Ver logs em tempo real$(NC)"
	@echo "  make logs"
	@echo ""
	@echo "  $(YELLOW)# Escalar para 3 réplicas$(NC)"
	@echo "  make scale REPLICAS=3"
	@echo ""
	@echo "  $(YELLOW)# Configurar para usar 1GB de RAM por 1 hora$(NC)"
	@echo "  make config-memory MB=1000"
	@echo "  make config-duration SEC=3600"
	@echo ""
	@echo "  $(YELLOW)# Executar teste intensivo$(NC)"
	@echo "  make test-intense"
	@echo ""
	@echo "  $(YELLOW)# Ciclo de desenvolvimento$(NC)"
	@echo "  # 1. Editar código"
	@echo "  nano memory_stress.py"
	@echo "  # 2. Rebuild e restart"
	@echo "  make dev"
	@echo ""
	@echo "  $(YELLOW)# Desinstalar tudo$(NC)"
	@echo "  make clean"
	@echo "  make clean"
	@echo ""
	@echo "$(GREEN)WORKFLOW RECOMENDADO:$(NC)"
	@echo ""
	@echo "  1. $(BLUE)make install$(NC)              → Instala tudo pela primeira vez"
	@echo "  2. $(BLUE)make status$(NC)               → Verifica se está rodando"
	@echo "  3. $(BLUE)make logs$(NC)                 → Acompanha execução"
	@echo "  4. $(BLUE)make test-basic$(NC)           → Executa teste básico"
	@echo "  5. $(BLUE)make top$(NC)                  → Monitora recursos"
	@echo "  6. $(BLUE)make uninstall$(NC)            → Remove quando terminar"
	@echo ""
	@echo "$(GREEN)TROUBLESHOOTING:$(NC)"
	@echo ""
	@echo "  $(YELLOW)Pod não inicia?$(NC)"
	@echo "    make describe"
	@echo "    make events"
	@echo ""
	@echo "  $(YELLOW)Ver logs de erro?$(NC)"
	@echo "    make logs-tail"
	@echo ""
	@echo "  $(YELLOW)Problemas com imagem?$(NC)"
	@echo "    make build"
	@echo "    make import"
	@echo ""
	@echo "  $(YELLOW)MicroK8s não responde?$(NC)"
	@echo "    make check-microk8s"
	@echo ""
	@echo "$(GREEN)DOCUMENTAÇÃO:$(NC)"
	@echo "  Para mais detalhes sobre cada comando, veja os comentários no Makefile"
	@echo "  ou execute: make [comando]"
	@echo ""
	@echo "$(BLUE)============================================================================$(NC)"
	@echo ""

.PHONY: check-microk8s
check-microk8s: ## Verifica se MicroK8s está instalado e rodando
	@echo "$(YELLOW)Verificando MicroK8s...$(NC)"
	@command -v microk8s >/dev/null 2>&1 || { echo "$(RED)❌ MicroK8s não encontrado!$(NC)"; exit 1; }
	@microk8s status --wait-ready >/dev/null 2>&1 || { echo "$(RED)❌ MicroK8s não está rodando!$(NC)"; exit 1; }
	@echo "$(GREEN)✓ MicroK8s está rodando$(NC)"

.PHONY: setup
setup: check-microk8s ## Configura o ambiente (addons, kubeconfig)
	@echo "$(YELLOW)Configurando ambiente...$(NC)"
	@microk8s enable dns
	@microk8s enable metrics-server
	@mkdir -p ~/.kube
	@microk8s config > ~/.kube/config
	@export KUBECONFIG=~/.kube/config
	@echo "$(GREEN)✓ Ambiente configurado$(NC)"

.PHONY: build
build: ## Faz build da imagem Docker
	@echo "$(YELLOW)Building imagem Docker...$(NC)"
	@$(DOCKER) build -t $(IMAGE_NAME) .
	@echo "$(GREEN)✓ Imagem criada: $(IMAGE_NAME)$(NC)"

.PHONY: build-registry
build-registry: setup ## Faz build e push para registry local do MicroK8s
	@echo "$(YELLOW)Habilitando registry...$(NC)"
	@microk8s enable registry
	@echo "$(YELLOW)Building e enviando para registry local...$(NC)"
	@$(DOCKER) build -t $(REGISTRY_IMAGE) .
	@$(DOCKER) push $(REGISTRY_IMAGE)
	@echo "$(GREEN)✓ Imagem enviada para registry local$(NC)"

.PHONY: import
import: build ## Importa imagem para o MicroK8s
	@echo "$(YELLOW)Importando imagem para MicroK8s...$(NC)"
	@$(DOCKER) save $(IMAGE_NAME) > memory-stress.tar
	@microk8s ctr image import memory-stress.tar
	@rm -f memory-stress.tar
	@echo "$(GREEN)✓ Imagem importada$(NC)"

.PHONY: deploy
deploy: import ## Faz deploy completo da aplicação
	@echo "$(YELLOW)Fazendo deploy da aplicação...$(NC)"
	@$(KUBECTL) apply -f $(DEPLOYMENT_FILE)
	@echo "$(GREEN)✓ Deploy realizado$(NC)"
	@echo "$(YELLOW)Aguardando pods ficarem prontos...$(NC)"
	@$(KUBECTL) wait --for=condition=ready pod -l app=memory-stress -n $(NAMESPACE) --timeout=120s || true
	@echo "$(GREEN)✓ Aplicação está rodando!$(NC)"

.PHONY: install
install: setup build import deploy ## Instalação completa (setup + build + deploy)
	@echo ""
	@echo "$(GREEN)=========================================="
	@echo "✓ Instalação completa!"
	@echo "==========================================$(NC)"
	@$(MAKE) status

.PHONY: uninstall
uninstall: ## Remove completamente a aplicação
	@echo "$(RED)Removendo aplicação...$(NC)"
	@$(KUBECTL) delete namespace $(NAMESPACE) --ignore-not-found=true
	@$(KUBECTL) delete -f $(DEPLOYMENT_FILE) --ignore-not-found=true
	@echo "$(YELLOW)Aguardando namespace ser removido...$(NC)"
	@while $(KUBECTL) get namespace $(NAMESPACE) >/dev/null 2>&1; do sleep 1; done
	@echo "$(GREEN)✓ Aplicação removida$(NC)"

.PHONY: clean
clean: uninstall ## Remove aplicação e imagens Docker
	@echo "$(YELLOW)Removendo imagens Docker...$(NC)"
	@$(DOCKER) rmi $(IMAGE_NAME) 2>/dev/null || true
	@$(DOCKER) rmi $(REGISTRY_IMAGE) 2>/dev/null || true
	@microk8s ctr images rm docker.io/library/memory-stress:latest 2>/dev/null || true
	@microk8s ctr images rm $(REGISTRY_IMAGE) 2>/dev/null || true
	@rm -f memory-stress.tar
	@echo "$(GREEN)✓ Limpeza completa$(NC)"

.PHONY: status
status: ## Mostra status da aplicação
	@echo ""
	@echo "$(BLUE)=========================================="
	@echo "Status da Aplicação"
	@echo "==========================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Pods:$(NC)"
	@$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "  Namespace não existe"
	@echo ""
	@echo "$(YELLOW)Deployments:$(NC)"
	@$(KUBECTL) get deployments -n $(NAMESPACE) 2>/dev/null || echo "  Namespace não existe"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@$(KUBECTL) get services -n $(NAMESPACE) 2>/dev/null || echo "  Namespace não existe"
	@echo ""
	@echo "$(YELLOW)HPA:$(NC)"
	@$(KUBECTL) get hpa -n $(NAMESPACE) 2>/dev/null || echo "  Namespace não existe"
	@echo ""

.PHONY: logs
logs: ## Mostra logs da aplicação em tempo real
	@echo "$(YELLOW)Logs da aplicação (Ctrl+C para sair):$(NC)"
	@$(KUBECTL) logs -f deployment/$(APP_NAME) -n $(NAMESPACE)

.PHONY: logs-tail
logs-tail: ## Mostra últimas 100 linhas dos logs
	@$(KUBECTL) logs deployment/$(APP_NAME) -n $(NAMESPACE) --tail=100

.PHONY: top
top: ## Mostra uso de recursos (CPU/Memória)
	@echo "$(YELLOW)Uso de recursos:$(NC)"
	@$(KUBECTL) top pods -n $(NAMESPACE)

.PHONY: describe
describe: ## Mostra detalhes completos dos pods
	@$(KUBECTL) describe pod -n $(NAMESPACE)

.PHONY: shell
shell: ## Abre shell dentro do pod
	@echo "$(YELLOW)Abrindo shell no pod...$(NC)"
	@$(KUBECTL) exec -it deployment/$(APP_NAME) -n $(NAMESPACE) -- /bin/bash

.PHONY: restart
restart: ## Reinicia a aplicação
	@echo "$(YELLOW)Reiniciando aplicação...$(NC)"
	@$(KUBECTL) rollout restart deployment/$(APP_NAME) -n $(NAMESPACE)
	@$(KUBECTL) rollout status deployment/$(APP_NAME) -n $(NAMESPACE)
	@echo "$(GREEN)✓ Aplicação reiniciada$(NC)"

.PHONY: scale
scale: ## Escala a aplicação (uso: make scale REPLICAS=3)
	@echo "$(YELLOW)Escalando para $(REPLICAS) réplicas...$(NC)"
	@$(KUBECTL) scale deployment/$(APP_NAME) --replicas=$(REPLICAS) -n $(NAMESPACE)
	@echo "$(GREEN)✓ Aplicação escalada$(NC)"

.PHONY: config-memory
config-memory: ## Configura memória target (uso: make config-memory MB=800)
	@echo "$(YELLOW)Configurando memória para $(MB)MB...$(NC)"
	@$(KUBECTL) set env deployment/$(APP_NAME) MEMORY_TARGET_MB=$(MB) -n $(NAMESPACE)
	@echo "$(GREEN)✓ Configuração aplicada$(NC)"

.PHONY: config-duration
config-duration: ## Configura duração do teste (uso: make config-duration SEC=1800)
	@echo "$(YELLOW)Configurando duração para $(SEC) segundos...$(NC)"
	@$(KUBECTL) set env deployment/$(APP_NAME) DURATION_SECONDS=$(SEC) -n $(NAMESPACE)
	@echo "$(GREEN)✓ Configuração aplicada$(NC)"

.PHONY: test-basic
test-basic: ## Teste básico: 500MB por 10 minutos
	@echo "$(BLUE)Executando teste básico (500MB, 10min)...$(NC)"
	@$(KUBECTL) set env deployment/$(APP_NAME) MEMORY_TARGET_MB=500 DURATION_SECONDS=600 -n $(NAMESPACE)
	@$(MAKE) logs

.PHONY: test-intense
test-intense: ## Teste intensivo: 800MB por 30 minutos
	@echo "$(BLUE)Executando teste intensivo (800MB, 30min)...$(NC)"
	@$(KUBECTL) set env deployment/$(APP_NAME) MEMORY_TARGET_MB=800 DURATION_SECONDS=1800 -n $(NAMESPACE)
	@$(MAKE) logs

.PHONY: test-oom
test-oom: ## Teste OOMKill: forçar limite de memória
	@echo "$(RED)Executando teste de OOMKill (1500MB)...$(NC)"
	@$(KUBECTL) set env deployment/$(APP_NAME) MEMORY_TARGET_MB=1500 DURATION_SECONDS=300 -n $(NAMESPACE)
	@$(MAKE) logs

.PHONY: events
events: ## Mostra eventos do namespace
	@$(KUBECTL) get events -n $(NAMESPACE) --sort-by='.lastTimestamp'

.PHONY: watch
watch: ## Monitora pods em tempo real
	@watch -n 2 '$(KUBECTL) get pods -n $(NAMESPACE)'

.PHONY: dev
dev: build import restart logs ## Modo desenvolvimento: build, import, restart e logs

.PHONY: info
info: ## Mostra informações úteis
	@echo ""
	@echo "$(BLUE)=========================================="
	@echo "Informações do Sistema"
	@echo "==========================================$(NC)"
	@echo ""
	@echo "$(YELLOW)MicroK8s:$(NC)"
	@microk8s version || echo "  Não disponível"
	@echo ""
	@echo "$(YELLOW)Kubectl:$(NC)"
	@$(KUBECTL) version --short 2>/dev/null || echo "  Não disponível"
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@$(DOCKER) --version || echo "  Não disponível"
	@echo ""
	@echo "$(YELLOW)Nodes:$(NC)"
	@$(KUBECTL) get nodes
	@echo ""
	@echo "$(YELLOW)Namespaces:$(NC)"
	@$(KUBECTL) get namespaces
	@echo ""

# Valores padrão
REPLICAS ?= 1
MB ?= 500
SEC ?= 3600