#!/usr/bin/env python3

import requests
import re
from collections import defaultdict
from typing import Dict, List, Set

def get_available_metrics(cadvisor_url: str = "http://localhost:8080") -> Dict[str, List[str]]:
    """Obtém todas as métricas disponíveis do cAdvisor"""
    
    try:
        response = requests.get(f"{cadvisor_url}/metrics", timeout=30)
        response.raise_for_status()
        
        metrics_text = response.text
        metrics_by_category = defaultdict(list)
        unique_metrics = set()
        
        for line in metrics_text.split('\n'):
            line = line.strip()
            
            # Ignorar comentários e linhas vazias
            if not line or line.startswith('#'):
                continue
            
            # Extrair nome da métrica
            if '{' in line:
                metric_name = line.split('{')[0]
            else:
                metric_name = line.split()[0]
            
            if metric_name and metric_name not in unique_metrics:
                unique_metrics.add(metric_name)
                
                # Categorizar métricas
                if 'cpu' in metric_name:
                    metrics_by_category['CPU'].append(metric_name)
                elif 'memory' in metric_name:
                    metrics_by_category['Memory'].append(metric_name)
                elif 'network' in metric_name:
                    metrics_by_category['Network'].append(metric_name)
                elif 'fs' in metric_name or 'disk' in metric_name:
                    metrics_by_category['Filesystem/Disk'].append(metric_name)
                elif 'process' in metric_name or 'thread' in metric_name:
                    metrics_by_category['Process'].append(metric_name)
                elif 'accelerator' in metric_name:
                    metrics_by_category['Accelerator/GPU'].append(metric_name)
                elif 'hugetlb' in metric_name:
                    metrics_by_category['HugeTLB'].append(metric_name)
                elif 'tcp' in metric_name or 'udp' in metric_name:
                    metrics_by_category['TCP/UDP'].append(metric_name)
                elif 'machine' in metric_name:
                    metrics_by_category['Machine'].append(metric_name)
                else:
                    metrics_by_category['Other'].append(metric_name)
        
        return dict(metrics_by_category)
        
    except Exception as e:
        print(f"Erro ao obter métricas: {e}")
        return {}

def compare_with_expected(available_metrics: Dict[str, List[str]]) -> None:
    """Compara métricas disponíveis com as esperadas"""
    
    from full_metrics_config import FullMetricsConfig
    
    config = FullMetricsConfig()
    expected_metrics = set(config.get_all_metrics())
    
    # Obter todas as métricas disponíveis
    available_set = set()
    for category_metrics in available_metrics.values():
        available_set.update(category_metrics)
    
    # Comparar
    missing_metrics = expected_metrics - available_set
    extra_metrics = available_set - expected_metrics
    
    print("\n" + "="*60)
    print("COMPARAÇÃO COM MÉTRICAS ESPERADAS")
    print("="*60)
    
    print(f"\n✅ Métricas esperadas encontradas: {len(expected_metrics & available_set)}")
    print(f"❌ Métricas esperadas não encontradas: {len(missing_metrics)}")
    print(f"➕ Métricas extras disponíveis: {len(extra_metrics)}")
    
    if missing_metrics:
        print("\n🔍 Métricas esperadas não encontradas:")
        for metric in sorted(missing_metrics):
            print(f"  - {metric}")
    
    if extra_metrics:
        print("\n🆕 Métricas extras disponíveis:")
        for metric in sorted(list(extra_metrics)[:10]):  # Mostrar apenas 10
            print(f"  - {metric}")
        if len(extra_metrics) > 10:
            print(f"  ... e mais {len(extra_metrics) - 10} métricas")

def main():
    print("🔍 Verificador de Métricas do cAdvisor")
    print("="*50)
    
    # Obter métricas disponíveis
    print("📊 Obtendo métricas disponíveis...")
    metrics = get_available_metrics()
    
    if not metrics:
        print("❌ Não foi possível obter métricas")
        print("Verifique se o cAdvisor está rodando em localhost:8080")
        return
    
    # Mostrar métricas por categoria
    total_metrics = sum(len(category_metrics) for category_metrics in metrics.values())
    print(f"\n✅ Total de métricas encontradas: {total_metrics}")
    
    for category, category_metrics in metrics.items():
        print(f"\n📂 {category} ({len(category_metrics)} métricas):")
        for metric in sorted(category_metrics)[:5]:  # Mostrar apenas 5 por categoria
            print(f"  - {metric}")
        if len(category_metrics) > 5:
            print(f"  ... e mais {len(category_metrics) - 5} métricas")
    
    # Comparar com métricas esperadas
    try:
        compare_with_expected(metrics)
    except ImportError:
        print("\n⚠️  Arquivo full_metrics_config.py não encontrado")
        print("Não foi possível comparar com métricas esperadas")
    
    # Verificar métricas específicas importantes
    important_metrics = [
        'container_cpu_usage_seconds_total',
        'container_memory_usage_bytes',
        'container_network_receive_bytes_total',
        'container_fs_usage_bytes',
        'container_processes',
        'container_cpu_schedstat_run_seconds_total',
        'container_network_tcp_usage_total',
        'container_accelerator_memory_total_bytes'
    ]
    
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE MÉTRICAS IMPORTANTES")
    print("="*60)
    
    all_available = set()
    for category_metrics in metrics.values():
        all_available.update(category_metrics)
    
    for metric in important_metrics:
        status = "✅" if metric in all_available else "❌"
        print(f"{status} {metric}")

if __name__ == "__main__":
    main()