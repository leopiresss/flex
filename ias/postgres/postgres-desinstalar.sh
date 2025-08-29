# Limpar todos os recursos
kubectl delete deployment postgres-deployment -n stress-app
kubectl delete service postgres-service -n stress-app
kubectl delete configmap postgres-config -n stress-app
kubectl delete pvc postgres-pv-pvc -n stress-app


