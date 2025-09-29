#!/bin/bash

echo "=== TESTE DE VALIDAÇÃO ==="

# 1. Verificar sistema de arquivos
echo "1. Sistema de arquivos:"
mount | grep -E "on / " | grep -q "rw" && echo "✅ RW" || echo "❌ RO"

# 2. Verificar MicroK8s
echo "2. Status MicroK8s:"
microk8s status --wait-ready && echo "✅ OK" || echo "❌ FALHA"

# 3. Teste simples de pod
echo "3. Teste de pod simples:"
microk8s kubectl run test-pod --image=busybox --restart=Never --rm -it -- echo "Teste OK" && echo "✅ POD OK" || echo "❌ POD FALHA"

# 4. Aplicar cAdvisor
echo "4. Aplicando cAdvisor..."
cat > test-cadvisor.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: cadvisor-test
  namespace: default
spec:
  hostNetwork: true
  hostPID: true
  automountServiceAccountToken: false
  containers:
  - name: cadvisor
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    args:
      - --housekeeping_interval=30s
      - --disable_metrics=percpu,sched,tcp,udp
    securityContext:
      privileged: true
    volumeMounts:
    - name: rootfs
      mountPath: /rootfs
      readOnly: true
    - name: var-run
      mountPath: /var/run
      readOnly: true
    - name: sys
      mountPath: /sys
      readOnly: true
  volumes:
  - name: rootfs
    hostPath:
      path: /
  - name: var-run
    hostPath:
      path: /var/run
  - name: sys
    hostPath:
      path: /sys
  restartPolicy: Never
EOF

microk8s kubectl apply -f test-cadvisor.yaml
sleep 30
microk8s kubectl get pod cadvisor-test && echo "✅ CADVISOR OK" || echo "❌ CADVISOR FALHA"
microk8s kubectl delete -f test-cadvisor.yaml