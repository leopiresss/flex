 

#!/bin/bash 

  

# Atualiza os pacotes do sistema 

echo "🔄 Atualizando o sistema..." 

sudo apt update && sudo apt upgrade -y 

  

# Instala o Snapd se não estiver instalado 

if ! command -v snap &> /dev/null; then 

    echo "📦 Instalando snapd..." 

    sudo apt install snapd -y 

fi 

  

# Instala o MicroK8s 

echo "🚀 Instalando MicroK8s# Instala o MicroK8s" 

sudo snap install microk8s --classic 

  

# Instala o Kubectl 

echo "🚀 Instalando Kubectl..." 

sudo snap install kubectl 

  

# Adiciona o usuário atual ao grupo microk8s 

echo "👤 Adicionando o usuário ao grupo microk8s..." 

sudo usermod -a -G microk8s $USER 

sudo mkdir –p ~/.kube 

sudo chmod 0700 ~/.kube 

sudo chown -f -R $USER ~/.kube 

 

echo "⚙️ Criando Kube Config..." 

microk8s config > ~/.kube/config 

 

# Habilita alguns addons úteis 

echo "⚙️ Habilitando addons úteis..." 

sudo microk8s enable dns storage ingress 

microk8s enable dashboard 

microk8s disable rbac 

  

  

# Cria alias para kubectl 

echo "🔧 Criando alias para kubectl..." 

sudo snap alias microk8s.kubectl kubectl 

  

# Verifica o status do MicroK8s 

echo "📋 Verificando status do MicroK8s..." 

microk8s status --wait-ready 

  

echo "✅ Instalação concluída! Reinicie a sessão para aplicar as permissões de grupo." 
