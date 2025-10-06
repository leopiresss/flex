# Build da imagem
docker build -t degradacao-test:v1 .

# Se usar registry local do microk8s
microk8s ctr image import degradacao-test:v1

# Ou salvar e importar
docker save degradacao-test:v1 > degradacao-test.tar
microk8s ctr image import degradacao-test.tar