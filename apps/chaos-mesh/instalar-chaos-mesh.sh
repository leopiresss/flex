
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update

kubectl create ns chaos-mesh

helm install chaos-mesh chaos-mesh/chaos-mesh --namespace=chaos-mesh  --version 2.6 --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/var/snap/microk8s/common/run/containerd.sock
# helm install chaos-mesh chaos-mesh/chaos-mesh --namespace=chaos-mesh --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/host-run/containerd.sock

# helm install chaos-mesh chaos-mesh/chaos-mesh -n=chaos-mesh --version 2.6  --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/host-run/containerd.sock

kubectl apply -f rbac-chaos-mesh.yaml
kubectl create token account-chaos-mesh-manager-oivxb -n chaos-mesh
kubectl describe -n chaos-mesh secrets account-chaos-mesh-manager-oivxb -n chaos-mesh