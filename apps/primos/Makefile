# Makefile para deploy local do prime-server no microk8s

IMAGE_NAME = prime-server
TAG = latest
FULL_IMAGE = $(IMAGE_NAME):$(TAG)
NAMESPACE = default

.PHONY: help build import deploy status logs clean port-forward test

# Comando padrão
help:
	@echo "Comandos disponíveis:"
	@echo "  build         - Construir a imagem Docker"
	@echo "  import        - Importar imagem para o microk8s"
	@echo "  deploy        - Deploy completo (build + import + apply)"
	@echo "  status        - Ver status dos pods e services"
	@echo "  logs          - Ver logs da aplicação"
	@echo "  port-forward  - Fazer port-forward para acesso local"
	@echo "  test          - Testar a aplicação"
	@echo "  clean         - Remover deployment"
	@echo "  clean-all     - Remover deployment e imagem"

# Construir imagem Docker
build:
	@echo "Construindo imagem Docker..."
	docker build -t $(FULL_IMAGE) .
	@echo "✓ Imagem construída: $(FULL_IMAGE)"

# Importar imagem para microk8s
import: build
	@echo "Importando imagem para microk8s..."
	docker save $(FULL_IMAGE) > $(IMAGE_NAME).tar
	microk8s ctr image import $(IMAGE_NAME).tar
	rm $(IMAGE_NAME).tar
	@echo "✓ Imagem importada no microk8s"

# Deploy completo
deploy: import
	@echo "Aplicando deployment..."
	microk8s kubectl apply -f deployment.yaml -n $(NAMESPACE)
	@echo "Aguardando pods ficarem prontos..."
	microk8s kubectl wait --for=condition=ready pod -l app=$(IMAGE_NAME) -n $(NAMESPACE) --timeout=60s
	@echo "✓ Deploy concluído!"
	@make status

# Ver status
status:
	@echo "=== STATUS ==="
	@echo "Pods:"
	@microk8s kubectl get pods -l app=$(IMAGE_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "Services:"
	@microk8s kubectl get svc -l app=$(IMAGE_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "Endpoints:"
	@microk8s kubectl get endpoints -l app=$(IMAGE_NAME) -n $(NAMESPACE)

# Ver logs
logs:
	microk8s kubectl logs -l app=$(IMAGE_NAME) -f -n $(NAMESPACE)

# Port-forward para acesso local
port-forward:
	@echo "Port-forward ativo em http://localhost:8080"
	@echo "Pressione Ctrl+C para parar"
	microk8s kubectl port-forward service/$(IMAGE_NAME)-service 8080:80 -n $(NAMESPACE)

# Testar aplicação
test:
	@echo "Testando aplicação..."
	@echo "Fazendo port-forward temporário..."
	@microk8s kubectl port-forward service/$(IMAGE_NAME)-service 8080:80 -n $(NAMESPACE) &
	@sleep 3
	@echo "Testando endpoint..."
	@curl -s http://localhost:8080 || echo "Endpoint não respondeu"
	@pkill -f "kubectl port-forward" || true

# Limpar deployment
clean:
	@echo "Removendo deployment..."
	microk8s kubectl delete -f deployment.yaml -n $(NAMESPACE) || true
	@echo "✓ Deployment removido"

# Limpar tudo (deployment + imagem)
clean-all: clean
	@echo "Removendo imagem do microk8s..."
	@microk8s ctr images rm docker.io/library/$(FULL_IMAGE) || true
	@echo "Removendo imagem do Docker..."
	@docker rmi $(FULL_IMAGE) || true
	@echo "✓ Limpeza completa realizada"

# Debug - ver imagens disponíveis
debug-images:
	@echo "=== IMAGENS DOCKER ==="
	@docker images | grep $(IMAGE_NAME) || echo "Nenhuma imagem encontrada"
	@echo ""
	@echo "=== IMAGENS MICROK8S ==="
	@microk8s ctr images ls | grep $(IMAGE_NAME) || echo "Nenhuma imagem encontrada"

# Verificar saúde do cluster
health:
	@echo "=== SAÚDE DO CLUSTER ==="
	@microk8s status
	@echo ""
	@echo "Nodes:"
	@microk8s kubectl get nodes
	@echo ""
	@echo "Pods no sistema:"
	@microk8s kubectl get pods --all-namespaces | head -10