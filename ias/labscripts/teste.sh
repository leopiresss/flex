#!/bin/bash

# Define o nome do arquivo onde a informação será gravada
ARQUIVO=~/flex/logs/log_do_sistema.txt

# Obtém a data e hora atual no formato YYYY-MM-DD HH:MM:SS
# O comando date com "+%F %T" é um atalho para ano-mes-dia e hora:minuto:segundo
DATA_HORA=$(date +"%Y-%m-%d %H:%M:%S")

# Obtém o nome do sistema operacional (ex: GNU/Linux)
NOME_OS=$(uname -o)

# Gera a linha com data, hora e nome do SO, e anexa ao arquivo
echo "${DATA_HORA} - ${NOME_OS}" >> "$ARQUIVO"
cat "$ARQUIVO"

echo "Informação adicionada ao arquivo '$ARQUIVO' com sucesso:"
echo "${DATA_HORA} - ${NOME_OS}"