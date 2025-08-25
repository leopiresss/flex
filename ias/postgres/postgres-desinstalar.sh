# Limpar todos os recursos
kubectl delete deployment postgres-deployment --ignore-not-found=true
kubectl delete service postgres-service --ignore-not-found=true
kubectl delete configmap postgres-config --ignore-not-found=true
kubectl delete secret postgres-secret --ignore-not-found=true
kubectl delete pvc postgres-pvc --ignore-not-found=true
kubectl delete pv postgres-pv --ignore-not-found=true

