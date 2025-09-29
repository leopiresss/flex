# Limpar todos os recursos
<<<<<<< HEAD
#kubectl delete deployment postgres-deployment --ignore-not-found=true
#kubectl delete service postgres-service --ignore-not-found=true
#kubectl delete pvc postgres-pvc --ignore-not-found=true
#kubectl delete pv postgres-pv --ignore-not-found=true
#kubectl delete configmap postgres-config --ignore-not-found=true
#kubectl delete secret postgres-secret --ignore-not-found=true
=======
kubectl delete deployment postgres-deployment -n stress-app
kubectl delete service postgres-service -n stress-app
kubectl delete configmap postgres-config -n stress-app
kubectl delete pvc postgres-pvc -n stress-app
kubectl delete pv postgres-pv -n stress-app

>>>>>>> a544ab9a6ffef55216bbafc0d40552851ba82368

