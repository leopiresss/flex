#!/bin/bash

# Script para corrigir problemas comuns de Makefile

echo "🔧 Corrigindo problemas do Makefile..."

# Verificar se o Makefile existe
if [ ! -f "Makefile" ] && [ ! -f "makefile" ]; then
    echo "❌ Makefile não encontrado no diretório atual"
    echo "💡 Certifique-se de estar no diretório correto"
    exit 1
fi

# Usar o nome correto do arquivo
MAKEFILE="Makefile"
if [ -f "makefile" ]; then
    MAKEFILE="makefile"
fi

echo "📁 Usando arquivo: $MAKEFILE"

# Backup do arquivo original
cp "$MAKEFILE" "${MAKEFILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 Backup criado: ${MAKEFILE}.backup.*"

# Verificar se há problemas de indentação (espaços em vez de tabs)
if grep -P "^ " "$MAKEFILE" > /dev/null; then
    echo "⚠️ Encontrados espaços em vez de tabs - corrigindo..."
    
    # Converter espaços iniciais em tabs (assumindo 4 espaços = 1 tab)
    sed -i 's/^    /\t/g' "$MAKEFILE"
    sed -i 's/^        /\t\t/g' "$MAKEFILE"
    
    echo "✅ Indentação corrigida"
else
    echo "✅ Indentação parece estar correta"
fi

# Testar sintaxe do Makefile
echo "🧪 Testando sintaxe do Makefile..."

if make -n help > /dev/null 2>&1; then
    echo "✅ Sintaxe do Makefile está correta!"
    echo ""
    echo "🎯 Comandos disponíveis:"
    make help
else
    echo "❌ Ainda há problemas de sintaxe no Makefile"
    echo ""
    echo "🔍 Verificando problemas específicos..."
    
    # Verificar problemas comuns
    echo "Verificando linha por linha..."
    make -n help 2>&1 | head -10
    
    echo ""
    echo "💡 Problemas comuns e soluções:"
    echo "1. Usar tabs (não espaços) para indentação"
    echo "2. Verificar se todas as linhas de comando começam com tab"
    echo "3. Verificar se não há caracteres especiais invisíveis"
    echo ""
    echo "🔄 Tentando criar um Makefile básico funcional..."
    
    # Criar um Makefile mínimo funcional
    cat > "${MAKEFILE}.minimal" << 'EOF'
# Makefile mínimo para Prime Server
IMAGE_NAME ?= prime-server
IMAGE_TAG ?= latest
REGISTRY ?= localhost:5000
NAMESPACE ?= default

help:
	@echo "🚀 Prime Server Kubernetes Deployment"
	@echo "Available commands:"
	@echo "  make build         # Build Docker image"
	@echo "  make deploy-simple # Simple deploy"
	@echo "  make test-simple   # Simple test"
	@echo "  make clean-simple  # Simple cleanup"

build:
	docker build -t $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) .

deploy-simple:
	kubectl apply -f deployment.yaml
	kubectl apply -f service.yaml

test-simple:
	kubectl get pods -l app=prime-server

clean-simple:
	kubectl delete -f service.yaml || true
	kubectl delete -f deployment.yaml || true
EOF
    
    echo "✅ Makefile mínimo criado: ${MAKEFILE}.minimal"
    echo "💡 Teste com: make -f ${MAKEFILE}.minimal help"
fi

echo ""
echo "🎯 PRÓXIMOS PASSOS:"
echo "==================="

if make -n help > /dev/null 2>&1; then
    echo "✅ Makefile está funcionando! Pode executar:"
    echo ""
    echo "# Para desenvolvimento local (sem registry):"
    echo "make deploy-no-push"
    echo ""
    echo "# Para setup completo com registry local:"
    echo "make deploy-auto"
    echo ""
    echo "# Para ver status:"
    echo "make status"
else
    echo "❌ Makefile ainda tem problemas. Opções:"
    echo ""
    echo "1. Usar Makefile mínimo:"
    echo "   make -f ${MAKEFILE}.minimal deploy-simple"
    echo ""
    echo "2. Executar comandos manualmente:"
    echo "   docker build -t prime-server:latest ."
    echo "   kubectl apply -f deployment.yaml"
    echo "   kubectl apply -f service.yaml"
    echo ""
    echo "3. Recriar Makefile do zero"
fi

echo ""
echo "📋 Arquivos de backup criados:"
ls -la ${MAKEFILE}.backup.* 2>/dev/null || echo "Nenhum backup anterior"

echo ""
echo "🔧 Script de correção concluído!"