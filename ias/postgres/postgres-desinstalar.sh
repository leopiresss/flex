# Limpar todos os recursos
kubectl delete deployment postgres-deployment -n stress-app
kubectl delete service postgres-service -n stress-app
kubectl delete configmap postgres-config -n stress-app
kubectl delete pvc postgres-pvc -n stress-app
kubectl delete pv postgres-pv -n stress-app


