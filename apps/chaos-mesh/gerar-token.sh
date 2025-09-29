kubectl apply -f rbac-chaos-mesh.yaml
kubectl create token account-chaos-mesh-manager-oivxb -n chaos-mesh > token-chaos-mesh.txt
echo "Token salvo em token-chaos-mesh.txt"