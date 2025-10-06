# Variáveis
APP_NAME = degradation-app
VERSION = 1.0.0
DOCKER_REGISTRY = localhost:5000

# Comandos principais
.PHONY: all build deploy clean help

# Help target should be the default
.DEFAULT_GOAL := help

# Help
help:
	@echo "🔍 Available commands:"
	@echo "  make build    - Build the application docker image"
	@echo "  make deploy   - Deploy the application to kubernetes"
	@echo "  make all      - Build and deploy"
	@echo "  make clean    - Remove docker images and k8s resources"
	@echo "  make help     - Show this help message"

all: build deploy

# Build da aplicação
build:
	@echo "🏗️ Building $(APP_NAME)..."
	./build.sh

# Deploy da aplicação
deploy:
	@echo "🚀 Deploying $(APP_NAME)..."
	./deploy.sh

# Limpa recursos
clean:
	@echo "🧹 Cleaning up..."
	docker rmi $(APP_NAME):$(VERSION) || true
	kubectl delete -f deployment.yaml