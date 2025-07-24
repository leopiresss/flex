#Instala o csadvisor e o dashboard do Microk8s
# é utilizado o cadvisor.yml como pod
# o token gerado pelo script deve ser utilizado na interface do dashboard

echo "⚙️ Gerando o token do dashboard..." 

microk8s kubectl describe secret -n kube-system microk8s-dashboard-token 

echo "⚙️ Ativando o cadvisor para métricas..." 

kubectl apply -f cadvisor.yml

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



echo "⚙️ Disponibilizando o dashboard do Microk8s.../n" 
microk8s kubectl port-forward --address 0.0.0.0 -n kube-system service/kubernetes-dashboard 10443:443 > /dev/null 2>&1 & 
 

