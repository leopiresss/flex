cd ~/flex/ias/microk8s/
./instalar-microk8s.sh

cd ~/flex/ias/cadvisor/
./instalar-cadvisor.sh

cd ~/flex/apps/stress-cpu/
./instalar-stress-cpu.sh

cd ~/flex/ias/prometheus_helm/
make install-all &
make port-forward &