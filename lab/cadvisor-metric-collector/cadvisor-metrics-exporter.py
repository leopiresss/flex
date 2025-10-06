#!/usr/bin/env python3
"""
Script para coletar métricas históricas de pods do Kubernetes via cAdvisor
e exportar para arquivo CSV.

Uso:
    python cadvisor_metrics_exporter.py --pod-name <nome-do-pod> [opções]
"""

import requests
import pandas as pd
import argparse
from datetime import datetime
import json
import sys
import warnings
warnings.filterwarnings('ignore')


class CAdvisorMetricsCollector:
    def __init__(self, cadvisor_url="http://localhost:8080", prometheus_url="http://localhost:9090"):
        """
        Inicializa o coletor de métricas.
        
        Args:
            cadvisor_url: URL do cAdvisor
            prometheus_url: URL do Prometheus
        """
        self.cadvisor_url = cadvisor_url.rstrip('/')
        self.prometheus_url = prometheus_url.rstrip('/')
    
    def get_container_stats_from_cadvisor(self, pod_name, namespace="default"):
        """
        Coleta estatísticas do cAdvisor diretamente.
        
        Args:
            pod_name: Nome do pod
            namespace: Namespace do pod
            
        Returns:
            dict com estatísticas do container
        """
        try:
            # cAdvisor expõe dados em /api/v2.0/stats ou /api/v1.3/docker/
            # Vamos tentar a API mais comum
            url = f"{self.cadvisor_url}/api/v2.0/stats?type=docker&recursive=true"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            stats = response.json()
            
            # Procura pelo container do pod
            matching_containers = []
            for container_name, container_stats in stats.items():
                if pod_name in container_name and namespace in container_name:
                    matching_containers.append({
                        'container_name': container_name,
                        'stats': container_stats
                    })
            
            return matching_containers
            
        except Exception as e:
            print(f"Erro ao coletar dados do cAdvisor: {e}")
            return []
    
    def query_prometheus(self, query, start_time=None, end_time=None, step='15s'):
        """
        Executa query no Prometheus.
        
        Args:
            query: Query PromQL
            start_time: Timestamp início (datetime ou string)
            end_time: Timestamp fim (datetime ou string)
            step: Intervalo entre pontos de dados
            
        Returns:
            Resultados da query
        """
        try:
            url = f"{self.prometheus_url}/api/v1/query_range"
            
            # Se não especificado, usa última hora
            if end_time is None:
                end_time = datetime.now()
            if start_time is None:
                from datetime import timedelta
                start_time = end_time - timedelta(hours=1)
            
            # Converte para timestamp
            if isinstance(start_time, datetime):
                start_time = start_time.timestamp()
            if isinstance(end_time, datetime):
                end_time = end_time.timestamp()
            
            params = {
                'query': query,
                'start': start_time,
                'end': end_time,
                'step': step
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'success':
                return data['data']['result']
            else:
                print(f"Erro na query: {data}")
                return []
                
        except Exception as e:
            print(f"Erro ao consultar Prometheus: {e}")
            return []
    
    def collect_metrics_from_prometheus(self, pod_name, namespace="default", 
                                       start_time=None, end_time=None, step='15s'):
        """
        Coleta métricas históricas via Prometheus.
        
        Args:
            pod_name: Nome do pod
            namespace: Namespace do pod
            start_time: Timestamp início
            end_time: Timestamp fim
            step: Intervalo entre medições
            
        Returns:
            DataFrame com as métricas
        """
        metrics_data = []
        
        # Queries PromQL para diferentes métricas
        queries = {
            # CPU - uso em cores
            'cpu_usage_cores': f'rate(container_cpu_usage_seconds_total{{pod="{pod_name}",namespace="{namespace}"}}[1m])',
            
            # CPU - porcentagem
            'cpu_usage_percent': f'rate(container_cpu_usage_seconds_total{{pod="{pod_name}",namespace="{namespace}"}}[1m]) * 100',
            
            # Memória - uso em bytes
            'memory_usage_bytes': f'container_memory_usage_bytes{{pod="{pod_name}",namespace="{namespace}"}}',
            
            # Memória - working set (memória realmente usada)
            'memory_working_set_bytes': f'container_memory_working_set_bytes{{pod="{pod_name}",namespace="{namespace}"}}',
            
            # Rede - bytes recebidos
            'network_receive_bytes': f'rate(container_network_receive_bytes_total{{pod="{pod_name}",namespace="{namespace}"}}[1m])',
            
            # Rede - bytes transmitidos
            'network_transmit_bytes': f'rate(container_network_transmit_bytes_total{{pod="{pod_name}",namespace="{namespace}"}}[1m])',
            
            # Rede - pacotes recebidos
            'network_receive_packets': f'rate(container_network_receive_packets_total{{pod="{pod_name}",namespace="{namespace}"}}[1m])',
            
            # Rede - pacotes transmitidos
            'network_transmit_packets': f'rate(container_network_transmit_packets_total{{pod="{pod_name}",namespace="{namespace}"}}[1m])',
        }
        print(queries)
        
        print(f"Coletando métricas do pod '{pod_name}' no namespace '{namespace}'...")
        
        all_data = {}
        
        for metric_name, query in queries.items():
            print(f"  Consultando: {metric_name}...")
            results = self.query_prometheus(query, start_time, end_time, step)
            
            if results:
                for result in results:
                    container = result['metric'].get('container', 'unknown')
                    values = result['values']
                    
                    for timestamp, value in values:
                        dt = datetime.fromtimestamp(timestamp)
                        key = (dt, container)
                        
                        if key not in all_data:
                            all_data[key] = {
                                'timestamp': dt,
                                'container': container,
                                'pod': pod_name,
                                'namespace': namespace
                            }
                        
                        all_data[key][metric_name] = float(value)
        
        if not all_data:
            print("Nenhum dado encontrado!")
            return pd.DataFrame()
        
        # Converte para DataFrame
        df = pd.DataFrame(list(all_data.values()))
        
        # Ordena por timestamp
        df = df.sort_values('timestamp')
        
        # Formata colunas de memória para MB
        if 'memory_usage_bytes' in df.columns:
            df['memory_usage_mb'] = df['memory_usage_bytes'] / (1024 * 1024)
        
        if 'memory_working_set_bytes' in df.columns:
            df['memory_working_set_mb'] = df['memory_working_set_bytes'] / (1024 * 1024)
        
        # Formata colunas de rede para KB/s
        if 'network_receive_bytes' in df.columns:
            df['network_receive_kb_s'] = df['network_receive_bytes'] / 1024
        
        if 'network_transmit_bytes' in df.columns:
            df['network_transmit_kb_s'] = df['network_transmit_bytes'] / 1024
        
        return df
    
    def export_to_csv(self, df, output_file):
        """
        Exporta DataFrame para CSV.
        
        Args:
            df: DataFrame com os dados
            output_file: Nome do arquivo de saída
        """
        if df.empty:
            print("Nenhum dado para exportar!")
            return False
        
        try:
            df.to_csv(output_file, index=False)
            print(f"\n✓ Dados exportados com sucesso para: {output_file}")
            print(f"  Total de registros: {len(df)}")
            print(f"  Período: {df['timestamp'].min()} até {df['timestamp'].max()}")
            print(f"\nColunas disponíveis:")
            for col in df.columns:
                print(f"  - {col}")
            return True
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Coleta métricas históricas de pods do Kubernetes via cAdvisor/Prometheus',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Coletar métricas da última hora
  python cadvisor_metrics_exporter.py --pod-name meu-pod

  # Especificar namespace
  python cadvisor_metrics_exporter.py --pod-name meu-pod --namespace production

  # Especificar período customizado (última 6 horas)
  python cadvisor_metrics_exporter.py --pod-name meu-pod --hours 6

  # Especificar URLs customizadas
  python cadvisor_metrics_exporter.py --pod-name meu-pod \\
    --prometheus-url http://prometheus:9090 \\
    --output metricas.csv
        """
    )
    
    parser.add_argument('--pod-name', required=True,
                       help='Nome do pod para coletar métricas')
    
    parser.add_argument('--namespace', default='default',
                       help='Namespace do pod (padrão: default)')
    
    parser.add_argument('--prometheus-url', default='http://localhost:9090',
                       help='URL do Prometheus (padrão: http://localhost:9090)')
    
    parser.add_argument('--cadvisor-url', default='http://localhost:8080',
                       help='URL do cAdvisor (padrão: http://localhost:8080)')
    
    parser.add_argument('--hours', type=int, default=1,
                       help='Número de horas de histórico para coletar (padrão: 1)')
    
    parser.add_argument('--step', default='15s',
                       help='Intervalo entre pontos de dados (padrão: 15s)')
    
    parser.add_argument('--output', default=None,
                       help='Nome do arquivo CSV de saída (padrão: <pod-name>_metrics_<timestamp>.csv)')
    
    args = parser.parse_args()
    
    # Define nome do arquivo de saída
    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{args.pod_name}_metrics_{timestamp}.csv"
    else:
        output_file = args.output
    
    # Calcula período
    from datetime import timedelta
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=args.hours)
    
    args.pod_name = 'app-degradacao-57f8dfd878-gdvk5'  # Alteração temporária para teste
    args.namespace = 'tcc-degradacao'  # Alteração temporária para teste
    args.prometheus_url = 'http://localhost:9090/'
    output_file = 'metricas_degradacao.csv'
    
    print("="*70)
    print("Coletor de Métricas do Kubernetes via cAdvisor/Prometheus")
    print("="*70)
    print(f"\nConfiguração:")
    print(f"  Pod: {args.pod_name}")
    print(f"  Namespace: {args.namespace}")
    print(f"  Prometheus: {args.prometheus_url}")
    print(f"  Período: {start_time} até {end_time}")
    print(f"  Step: {args.step}")
    print(f"  Arquivo de saída: {output_file}")
    print()
    
    # Inicializa coletor
    collector = CAdvisorMetricsCollector(
        cadvisor_url=args.cadvisor_url,
        prometheus_url=args.prometheus_url
    )
    
    # Coleta métricas
    df = collector.collect_metrics_from_prometheus(
        pod_name=args.pod_name,
        namespace=args.namespace,
        start_time=start_time,
        end_time=end_time,
        step=args.step
    )
    
    # Exporta para CSV
    if not df.empty:
        collector.export_to_csv(df, output_file)
        
        # Mostra estatísticas básicas
        print("\n" + "="*70)
        print("Estatísticas Resumidas:")
        print("="*70)
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            print(df[numeric_cols].describe())
    else:
        print("\n⚠ Nenhum dado foi coletado. Verifique:")
        print("  1. Se o Prometheus está acessível")
        print("  2. Se o nome do pod e namespace estão corretos")
        print("  3. Se existem métricas para o período especificado")
        sys.exit(1)


if __name__ == "__main__":
    main()