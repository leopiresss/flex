#Instala o csadvisor e o dashboard do Microk8s
# é utilizado o cadvisor.yml como pod
# o token gerado pelo script deve ser utilizado na interface do dashboard

echo "⚙️ Gerando o token do dashboard..." 
microk8s kubectl describe secret -n kube-system microk8s-dashboard-token 

echo "⚙️ Disponibilizando o dashboard do Microk8s.../n" 
microk8s kubectl port-forward --address 0.0.0.0 -n kube-system service/kubernetes-dashboard 10443:443 > /dev/null 2>&1 & 



echo "⚙️ Ativando o cadvisor para métricas..." 

kubectl apply -f ./cadvisor/cadvisor.yml

echo "Passo 1: Listando pods do cAdvisor no namespace kube-system..."

CADVISOR_POD=$(kubectl get pods -n kube-system | awk '/cadvisor/ {print $1}')

if [[ -z "$CADVISOR_POD" ]]; then
  echo "Nenhum pod do cAdvisor encontrado! Verifique a instalação."
  exit 1
fi

echo "Pod do cAdvisor encontrado: $CADVISOR_POD"

echo
echo "Passo 2: Realizando port-forward local da porta 8080 do pod $CADVISOR_POD..."

kubectl port-forward --address 0.0.0.0 -n kube-system pod/$CADVISOR_POD 8080:8080 > /dev/null 2>&1 &
PF_PID=$!
sleep 3  # Aguarda o port-forward estabilizar

echo
echo "Passo 3: Exibindo as últimas 20 linhas dos logs do pod $CADVISOR_POD:"
kubectl logs -n kube-system $CADVISOR_POD | tail -20

echo
echo "Passo 4: Verificando o endpoint /metrics do cAdvisor (primeiras 20 linhas):"
curl --silent http://localhost:8080/metrics | head -20
 

echo "=== ACESSANDO GRAFANA ==="

# 1. Verificar se o Grafana está rodando
echo "1. Verificando status do Grafana..."
microk8s kubectl get pods -n observability | grep grafana

# 2. Obter credenciais
echo -e "\n2. Obtendo credenciais..."
echo "Usuário: admin"
echo -n "Senha: "
microk8s kubectl get secret -n observability kube-prom-stack-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
echo

# 3. Verificar porta disponível
echo -e "\n3. Verificando portas disponíveis..."
if ! ss -tlpn | grep -q :3000; then
    PORT=3000
    echo "Usando porta 3000"
elif ! ss -tlpn | grep -q :3001; then
    PORT=3001
    echo "Usando porta 3001"
else
    PORT=3002
    echo "Usando porta 3002"
fi

# 4. Instruções finais
echo -e "\n4. Para acessar o Grafana:"
echo "Execute: microk8s kubectl port-forward -n observability svc/kube-prom-stack-grafana $PORT:80"
echo "Depois acesse: http://localhost:$PORT"
echo "Use as credenciais mostradas acima"
microk8s kubectl port-forward -n observability svc/kube-prom-stack-grafana $PORT:80  > /dev/null 2>&1 & 