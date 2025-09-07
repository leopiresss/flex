echo "Instalando microk8s ..."
cd ~/flex/ias/microk8s/
 ./instalar-microk8s.sh

echo "Instalando cadvisor ..."
cd ~/flex/ias/cadvisor/
 ./instalar-cadvisor.sh

echo "Instalando prometheus ..."
cd ~/flex/ias/prometheus/
./instalar-prometheus.sh


#cd  ../../apps/stress-cpu/
#echo "Instalando stress-cpu ..."
#./instalar-stress-cpu.sh