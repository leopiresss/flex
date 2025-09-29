# Makefile para instalação do Prometheus no MicroK8s
# Configurações
NAMESPACE = prometheus
RELEASE_NAME = prometheus
DOMAIN = prometheus.local
INGRESS_CLASS = nginx

.PHONY: help check-microk8s enable-addons add-helm-repo install-prometheus expose-nodeport expose-ingress status clean uninstall

# Comando padrão
help:
	@echo "Makefile para Prometheus no MicroK8s"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  check-microk8s    - Verificar status do MicroK8s"
	@echo "  enable-addons     - Habilitar addons necessários"
	@echo "  add-helm-repo     - Adicionar repositório do Prometheus"
	@echo "  install-prometheus - Instalar Prometheus"
	@echo "  expose-nodeport   - Expor via NodePort (acesso direto)"
	@echo "  expose-ingress    - Expor via Ingress (recomendado)"
	@echo "  status            - Verificar status da instalação"
	@echo "  port-forward      - Criar port-forward local (porta 9090)"
	@echo "  clean             - Limpar recursos"
	@echo "  uninstall         - Desinstalar completamente"
	@echo "  install-all       - Instalação completa (addons + prometheus + ingress)"

# Verificar se MicroK8s está rodando
check-microk8s:
	@echo "🔍 Verificando status do MicroK8s..."
	microk8s status --wait-ready
	microk8s kubectl get nodes

# Habilitar addons necessários
enable-addons:
	@echo "🔧 Habilitando addons do MicroK8s..."
	microk8s enable dns
	microk8s enable hostpath-storage
	microk8s enable helm3
	microk8s enable ingress
	@echo "✅ Addons habilitados!"

# Adicionar repositório do Helm
add-helm-repo:
	@echo "📦 Adicionando repositório do Prometheus..."
	microk8s helm3 repo add prometheus-community https://prometheus-community.github.io/helm-charts
	microk8s helm3 repo update
	@echo "✅ Repositório adicionado!"

# Instalar Prometheus
install-prometheus:
	@echo "🚀 Instalando Prometheus..."
	microk8s helm3 install $(RELEASE_NAME) prometheus-community/prometheus \
		--namespace $(NAMESPACE) \
		--create-namespace \
		--set server.persistentVolume.enabled=true \
		--set server.persistentVolume.size=1Gi \
		--set alertmanager.enabled=true \
		--set nodeExporter.enabled=true \
		--set pushgateway.enabled=true \
		--wait
	@echo "✅ Prometheus instalado!"

# Expor via NodePort (acesso direto via IP do nó)
expose-nodeport:
	@echo "🌐 Expondo Prometheus via NodePort..."
	microk8s kubectl patch svc $(RELEASE_NAME)-server -n $(NAMESPACE) -p '{"spec":{"type":"NodePort","ports":[{"port":80,"nodePort":30090,"targetPort":9090}]}}'
	@echo "✅ Prometheus exposto na porta 30090!"
	@echo "🔗 Acesse via: http://$(shell microk8s kubectl get nodes -o wide | grep -v NAME | head -1 | awk '{print $$6}'):30090"

# Expor via Ingress (recomendado para produção)
expose-ingress:
	@echo "🌐 Criando Ingress para Prometheus..."
	@cat <<EOF | microk8s kubectl apply -f - \n\
apiVersion: networking.k8s.io/v1\n\
kind: Ingress\n\
metadata:\n\
  name: prometheus-ingress\n\
  namespace: $(NAMESPACE)\n\
  annotations:\n\
    nginx.ingress.kubernetes.io/rewrite-target: /\n\
spec:\n\
  ingressClassName: $(INGRESS_CLASS)\n\
  rules:\n\
  - host: $(DOMAIN)\n\
    http:\n\
      paths:\n\
      - path: /\n\
        pathType: Prefix\n\
        backend:\n\
          service:\n\
            name: $(RELEASE_NAME)-server\n\
            port:\n\
              number: 80\n\
EOF
	@echo "✅ Ingress criado!"
	@echo "📝 Adicione ao /etc/hosts: $(shell microk8s kubectl get nodes -o wide | grep -v NAME | head -1 | awk '{print $$6}') $(DOMAIN)"
	@echo "🔗 Acesse via: http://$(DOMAIN)"

# Verificar status da instalação
status:
	@echo "📊 Status da instalação:"
	@echo ""
	@echo "Pods:"
	microk8s kubectl get pods -n $(NAMESPACE)
	@echo ""
	@echo "Services:"
	microk8s kubectl get svc -n $(NAMESPACE)
	@echo ""
	@echo "Ingress:"
	microk8s kubectl get ingress -n $(NAMESPACE) 2>/dev/null || echo "Nenhum Ingress encontrado"
	@echo ""
	@echo "PersistentVolumes:"
	microk8s kubectl get pv

# Criar port-forward para acesso local
port-forward:
	@echo "🔗 Criando port-forward na porta 9090..."
	@echo "Acesse http://localhost:9090"
	@echo "Pressione Ctrl+C para parar"
	microk8s kubectl port-forward -n $(NAMESPACE) svc/$(RELEASE_NAME)-server 9090:80

# Limpar recursos (manter PVs)
clean:
	@echo "🧹 Limpando recursos..."
	microk8s kubectl delete ingress prometheus-ingress -n $(NAMESPACE) 2>/dev/null || true
	@echo "✅ Recursos limpos!"

# Desinstalar completamente
uninstall:
	@echo "🗑️  Desinstalando Prometheus..."
	microk8s helm3 uninstall $(RELEASE_NAME) -n $(NAMESPACE) || true
	microk8s kubectl delete namespace $(NAMESPACE) || true
	@echo "✅ Prometheus desinstalado!"

# Instalação completa automatizada
install-all: check-microk8s enable-addons add-helm-repo install-prometheus expose-ingress status
	@echo ""
	@echo "🎉 Instalação completa do Prometheus finalizada!"
	@echo ""
	@echo "📋 Próximos passos:"
	@echo "1. Adicione ao /etc/hosts: $(shell microk8s kubectl get nodes -o wide | grep -v NAME | head -1 | awk '{print $$6}') $(DOMAIN)"
	@echo "2. Acesse: http://$(DOMAIN)"
	@echo "3. Ou use: make port-forward (para acesso local)"
	@echo ""
	@echo "📊 Para verificar status: make status"

# Configuração alternativa com LoadBalancer (se disponível)
expose-loadbalancer:
	@echo "⚡ Expondo via LoadBalancer..."
	microk8s kubectl patch svc $(RELEASE_NAME)-server -n $(NAMESPACE) -p '{"spec":{"type":"LoadBalancer"}}'
	@echo "✅ LoadBalancer configurado!"
	@echo "🔄 Aguardando IP externo..."
	microk8s kubectl get svc -n $(NAMESPACE) -w

# Backup da configuração
backup:
	@echo "💾 Criando backup da configuração..."
	mkdir -p backup
	microk8s helm3 get values $(RELEASE_NAME) -n $(NAMESPACE) > backup/prometheus-values.yaml
	microk8s kubectl get all -n $(NAMESPACE) -o yaml > backup/prometheus-resources.yaml
	@echo "✅ Backup criado na pasta backup/"