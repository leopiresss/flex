#!/usr/bin/env python3
"""
Script de diagnóstico avançado para cAdvisor
"""

import requests
import json
import sys
import os
from datetime import datetime

def check_cadvisor_endpoints():
    """Verifica todos os endpoints disponíveis do cAdvisor"""
    base_url = "http://localhost:8080"
    endpoints = [
        "/api/v1.3/machine",
        "/api/v1.3/containers",
        "/api/v1.3/containers/",
        "/api/v2.1/stats",
        "/healthz"
    ]
    
    print("=== Verificando Endpoints do cAdvisor ===")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"✅ {endpoint}: Status {response.status_code}")
            
            if endpoint == "/api/v1.3/machine" and response.status_code == 200:
                data = response.json()
                print(f"   Cores: {data.get('num_cores', 'N/A')}")
                print(f"   Memória: {data.get('memory_capacity', 0) / (1024**3):.2f} GB")
                
            elif endpoint == "/api/v1.3/containers" and response.status_code == 200:
                data = response.json()
                print(f"   Containers encontrados: {len(data)}")
                
                # Analisar estrutura do primeiro container
                if data:
                    first_container = list(data.items())[0]
                    path, info = first_container
                    print(f"   Primeiro container: {path}")
                    print(f"   Tipo de info: {type(info)}")
                    
                    if isinstance(info, dict):
                        print(f"   Chaves disponíveis: {list(info.keys())}")
                        
                        # Verificar stats
                        stats = info.get('stats', [])
                        print(f"   Stats: tipo={type(stats)}, quantidade={len(stats) if isinstance(stats, list) else 'N/A'}")
                        
                        if isinstance(stats, list) and stats:
                            latest = stats[-1]
                            print(f"   Último stat: tipo={type(latest)}")
                            if isinstance(latest, dict):
                                print(f"   Chaves do stat: {list(latest.keys())}")
                                print(f"   Timestamp: {latest.get('timestamp', 'N/A')}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: Erro - {e}")
        except json.JSONDecodeError as e:
            print(f"❌ {endpoint}: JSON inválido - {e}")
        except Exception as e:
            print(f"❌ {endpoint}: Erro inesperado - {e}")

def check_kubernetes_containers():
    """Verifica containers específicos do Kubernetes"""
    try:
        response = requests.get("http://localhost:8080/api/v1.3/containers", timeout=10)
        if response.status_code != 200:
            print("❌ Não foi possível obter lista de containers")
            return
        
        data = response.json()
        print(f"\n=== Análise de Containers Kubernetes ===")
        print(f"Total de containers: {len(data)}")
        
        k8s_containers = []
        system_containers = []
        other_containers = []
        
        for path, info in data.items():
            if not isinstance(info, dict):
                continue
                
            # Classificar containers
            if any(k8s_term in path.lower() for k8s_term in ['kube', 'kubernetes', 'pod']):
                k8s_containers.append(path)
            elif path == '/' or 'system' in path.lower():
                system_containers.append(path)
            else:
                other_containers.append(path)
        
        print(f"Containers Kubernetes: {len(k8s_containers)}")
        for container in k8s_containers[:5]:  # Mostrar apenas 5
            print(f"  - {container}")
        
        print(f"Containers do Sistema: {len(system_containers)}")
        for container in system_containers:
            print(f"  - {container}")
        
        print(f"Outros Containers: {len(other_containers)}")
        for container in other_containers[:5]:  # Mostrar apenas 5
            print(f"  - {container}")
            
    except Exception as e:
        print(f"❌ Erro ao analisar containers: {e}")

def test_specific_container():
    """Testa um container específico em detalhes"""
    try:
        response = requests.get("http://localhost:8080/api/v1.3/containers/", timeout=10)
        if response.status_code != 200:
            print("❌ Não foi possível obter dados do container raiz")
            return
        
        data = response.json()
        print(f"\n=== Teste Container Raiz (/) ===")
        
        if '/' in data:
            container_info = data['/']
            print(f"Tipo de dados: {type(container_info)}")
            
            if isinstance(container_info, dict):
                print(f"Chaves disponíveis: {list(container_info.keys())}")
                
                # Testar stats
                stats = container_info.get('stats', [])
                print(f"Stats: {len(stats)} registros")
                
                if stats and isinstance(stats, list):
                    latest = stats[-1]
                    print(f"Último stat timestamp: {latest.get('timestamp', 'N/A')}")
                    
                    # Verificar métricas específicas
                    cpu = latest.get('cpu', {})
                    memory = latest.get('memory', {})
                    network = latest.get('network', {})
                    
                    print(f"CPU disponível: {bool(cpu)}")
                    print(f"Memory disponível: {bool(memory)}")
                    print(f"Network disponível: {bool(network)}")
                    
                    if cpu:
                        usage = cpu.get('usage', {})
                        print(f"  CPU total usage: {usage.get('total', 'N/A')}")
                    
                    if memory:
                        print(f"  Memory usage: {memory.get('usage', 'N/A')}")
                        print(f"  Memory working_set: {memory.get('working_set', 'N/A')}")
                    
                    if network:
                        interfaces = network.get('interfaces', [])
                        print(f"  Network interfaces: {len(interfaces)}")
        
    except Exception as e:
        print(f"❌ Erro ao testar container específico: {e}")

def check_microk8s_status():
    """Verifica status do MicroK8s"""
    print(f"\n=== Status do MicroK8s ===")
    
    import subprocess
    
    try:
        # Verificar status do microk8s
        result = subprocess.run(['microk8s', 'status'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ MicroK8s está rodando")
            print(result.stdout)
        else:
            print("❌ MicroK8s não está rodando ou com problemas")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao verificar status do MicroK8s")
    except FileNotFoundError:
        print("❌ Comando 'microk8s' não encontrado")
    except Exception as e:
        print(f"❌ Erro ao verificar MicroK8s: {e}")
    
    try:
        # Verificar pods do sistema
        result = subprocess.run(['microk8s', 'kubectl', 'get', 'pods', '-A'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print("\n✅ Pods do sistema:")
            print(result.stdout)
        else:
            print("❌ Erro ao listar pods")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Erro ao listar pods: {e}")

def main():
    print("=== Diagnóstico Completo do cAdvisor ===")
    print(f"Timestamp: {datetime.now()}")
    
    # Verificar endpoints
    check_cadvisor_endpoints()
    
    # Analisar containers
    check_kubernetes_containers()
    
    # Testar container específico
    test_specific_container()
    
    # Verificar MicroK8s
    check_microk8s_status()
    
    print("\n=== Diagnóstico Concluído ===")

if __name__ == "__main__":
    main()