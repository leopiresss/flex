#!/usr/bin/env python3
"""
Script de teste para verificar conectividade e estrutura da API do cAdvisor
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from cadvisor_client import CAdvisorClient

def main():
    print("=== Teste de Conectividade cAdvisor ===")
    
    client = CAdvisorClient()
    
    # Teste 1: Conexão
    print("\n1. Testando conexão...")
    if not client.test_connection():
        print("❌ Falha na conexão")
        return 1
    print("✅ Conexão OK")
    
    # Teste 2: Informações da máquina
    print("\n2. Obtendo informações da máquina...")
    machine_info = client.get_machine_info()
    if machine_info:
        print(f"✅ CPUs: {machine_info.get('num_cores', 'N/A')}")
        print(f"✅ Memória: {machine_info.get('memory_capacity', 0) / (1024**3):.2f} GB")
    else:
        print("❌ Erro ao obter informações da máquina")
    
    # Teste 3: Snapshot único
    print("\n3. Coletando snapshot único...")
    snapshot = client.collect_single_snapshot()
    if snapshot:
        print(f"✅ Coletados dados de {len(snapshot)} containers")
        for i, container in enumerate(snapshot[:3]):  # Mostrar apenas 3 primeiros
            print(f"   Container {i+1}: {container['container_name']}")
    else:
        print("❌ Nenhum dado coletado")
    
    print("\n=== Teste Concluído ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())