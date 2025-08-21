#!/usr/bin/env python3

import requests
import json
import re
from typing import Dict, List, Optiona
from datetime import datetime

class cAdvisorPodDiscovery:
    """Descoberta e análise de pods no cAdvisor"""
    
    def __init__(self, cadvisor_url: str = "http://localhost:8080"):
        self.cadvisor_url = cadvisor_url.rstrip('/')
        self.session = requests.Session()
    
    def list_all_containers(self) -> Dict:
        """Lista todos os containers conhecidos pelo cAdvisor"""
        try:
            response = self.session.get(f"{self.cadvisor_url}/api/v1.3/containers")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao listar containers: {e}")
            return {}
    
    def find_pod_containers(self, pod_name: str) -> List[Dict]:
        """Encontra todos os containers de um pod específico"""
        containers = self.list_all_containers()
        pod_containers = []
        
        for container_path, container_data in containers.items():
            spec = container_data.get('spec', {})
            labels = spec.get('labels', {})
            
            # Verificar se pertence ao pod
            if self._is_pod_container(labels, pod_name):
                pod_containers.append({
                    'path': container_path,
                    'data': container_data,
                    'labels': labels
                })
        
        return pod_containers
    
    def _is_pod_container(self, labels: Dict, pod_name: str) -> bool:
        """Verifica se o container pertence ao pod"""
        pod_labels = [
            labels.get('io.kubernetes.pod.name'),
            labels.get('pod_name'),
            labels.get('pod')
        ]
        return pod_name in pod_labels
    
    def analyze_pod_structure(self, pod_name: str) -> None:
        """Analisa a estrutura completa de um pod"""
        print(f"🔍 Analisando estrutura do pod: {pod_name}")
        print("=" * 60)
        
        pod_containers = self.find_pod_containers(pod_name)
        
        if not pod_containers:
            print(f"❌ Pod '{pod_name}' não encontrado")
            print("\n💡 Pods disponíveis:")
            self.list_available_pods()
            return
        
        print(f"✅ Encontrados {len(pod_containers)} containers para o pod")
        
        for i, container in enumerate(pod_containers):
            print(f"\n🔹 Container {i+1}:")
            print(f"   Path: {container['path']}")
            
            labels = container['labels']
            print(f"   Labels:")
            for key, value in labels.items():
                if 'kubernetes' in key or 'pod' in key or 'container' in key:
                    print(f"     - {key}: {value}")
            
            # Verificar se tem estatísticas
            stats = container['data'].get('stats', [])
            print(f"   Estatísticas disponíveis: {len(stats)} pontos")
            
            if stats:
                latest = stats[-1]
                timestamp = latest.get('timestamp')
                print(f"   Última coleta: {timestamp}")
                
                # Verificar métricas disponíveis
                metrics = []
                if 'cpu' in latest:
                    metrics.append('CPU')
                if 'memory' in latest:
                    metrics.append('Memory')
                if 'network' in latest:
                    metrics.append('Network')
                if 'filesystem' in latest:
                    metrics.append('Filesystem')
                
                print(f"   Métricas: {', '.join(metrics)}")
    
    def list_available_pods(self) -> List[str]:
        """Lista todos os pods disponíveis"""
        containers = self.list_all_containers()
        pods = set()
        
        for container_path, container_data in containers.items():
            spec = container_data.get('spec', {})
            labels = spec.get('labels', {})
            
            pod_name = labels.get('io.kubernetes.pod.name')
            if pod_name:
                pods.add(pod_name)
        
        pods_list = sorted(list(pods))
        
        for pod in pods_list:
            print(f"  - {pod}")
        
        return pods_list
    
    def get_pod_metrics_paths(self, pod_name: str) -> List[str]:
        """Retorna os paths dos containers do pod para consultas diretas"""
        pod_containers = self.find_pod_containers(pod_name)
        return [container['path'] for container in pod_containers]
    
    def check_prometheus_metrics(self, pod_name: str) -> None:
        """Verifica métricas Prometheus disponíveis para o pod"""
        try:
            response = self.session.get(f"{self.cadvisor_url}/metrics")
            response.raise_for_status()
            
            metrics_text = response.text
            pod_metrics = []
            
            for line in metrics_text.split('\n'):
                if f'pod="{pod_name}"' in line or f'pod_name="{pod_name}"' in line:
                    # Extrair nome da métrica
                    if '{' in line:
                        metric_name = line.split('{')[0]
                    else:
                        metric_name = line.split()[0]
                    
                    if metric_name and metric_name not in pod_metrics:
                        pod_metrics.append(metric_name)
            
            print(f"\n📊 Métricas Prometheus para pod '{pod_name}':")
            print(f"Total: {len(pod_metrics)} métricas")
            
            # Agrupar por categoria
            categories = {
                'CPU': [m for m in pod_metrics if 'cpu' in m],
                'Memory': [m for m in pod_metrics if 'memory' in m],
                'Network': [m for m in pod_metrics if 'network' in m],
                'Filesystem': [m for m in pod_metrics if 'fs' in m],
                'Process': [m for m in pod_metrics if 'process' in m or 'thread' in m],
                'Other': [m for m in pod_metrics if not any(cat in m for cat in ['cpu', 'memory', 'network', 'fs', 'process', 'thread'])]
            }
            
            for category, metrics in categories.items():
                if metrics:
                    print(f"\n  {category} ({len(metrics)}):")
                    for metric in metrics[:5]:  # Mostrar apenas 5
                        print(f"    - {metric}")
                    if len(metrics) > 5:
                        print(f"    ... e mais {len(metrics) - 5} métricas")
        
        except Exception as e:
            print(f"Erro ao verificar métricas Prometheus: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Descoberta de pods no cAdvisor")
    parser.add_argument("--pod", help="Nome do pod para analisar")
    parser.add_argument("--list-pods", action="store_true", help="Listar todos os pods")
    parser.add_argument("--cadvisor-url", default="http://localhost:8080", help="URL do cAdvisor")
    
    args = parser.parse_args()
    
    discovery = cAdvisorPodDiscovery(args.cadvisor_url)
    
    # Testar conexão
    print(f"🔗 Testando conexão com {args.cadvisor_url}...")
    try:
        response = requests.get(f"{args.cadvisor_url}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ cAdvisor acessível")
        else:
            print("❌ cAdvisor não respondeu corretamente")
            return
    except:
        print("❌ Não foi possível conectar ao cAdvisor")
        print("Execute: microk8s kubectl port-forward -n monitoring svc/cadvisor 8080:8080")
        return
    
    if args.list_pods:
        print("\n📋 Pods disponíveis no cAdvisor:")
        discovery.list_available_pods()
    
    elif args.pod:
        discovery.analyze_pod_structure(args.pod)
        discovery.check_prometheus_metrics(args.pod)
        
        # Mostrar paths para consulta direta
        paths = discovery.get_pod_metrics_paths(args.pod)
        if paths:
            print(f"\n�� Paths para consulta direta:")
            for path in paths:
                print(f"  {args.cadvisor_url}/api/v1.3/containers{path}")
    
    else:
        print("Use --pod <nome> para analisar um pod específico")
        print("Use --list-pods para listar todos os pods")

if __name__ == "__main__":
    main()