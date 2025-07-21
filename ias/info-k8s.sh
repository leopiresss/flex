
#!/bin/bash

for ctx in $(kubectl config get-contexts -o name); do
  echo "Cluster: $ctx"
  kubectl --context $ctx get nodes -o custom-columns=NAME:.metadata.name,TIPO_AMBIENTE:.metadata.labels.tipo_de_ambiente
  kubectl --context $ctx top node --no-headers | awk '{print "Nó:", $1, "- CPU:", $2, "- Memória:", $4}'
  echo "---------------------------------------"
done