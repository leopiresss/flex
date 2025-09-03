echo "Instalando microk8s ..."
 ./ias/microk8s/instalar-microk8s.sh

echo "Instalando cadvisor ..."
cd ias/cadvisor/
 ./ias/cadvisor/instalar-cadvisor.sh

echo "Instalando prometheus ..."
cd ias/prometheus/
./instalar-prometheus.sh

cd  ../../apps/stress-cpu/
echo "Instalando stress-cpu ..."
./instalar-stress-cpu.sh