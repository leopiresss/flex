#!/usr/bin/env python3

import requests
import json
import pandas as pd
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import argparse
import logging
import sys
from dataclasses import dataclass
import time

@dataclass
class PodMetrics:
    """Estrutura para armazenar métricas do pod"""
    pod_name: str
    container_name: str
    namespace: str
    timestamp: datetime
    
    # CPU Metrics
    cpu_usage_total: float = 0.0
    cpu_usage_user: float = 0.0
    cpu_usage_system: float = 0.0
    cpu_usage_rate: float = 0.0
    cpu_load_average: float = 0.0
    cpu_throttled_seconds: float = 0.0
    cpu_throttled_periods: int = 0
    
    # Memory Metrics
    memory_usage: int = 0
    memory_working_set: int = 0
    memory_rss: int = 0
    memory_cache: int = 0
    memory_swap: int = 0
    memory_max_usage: int = 0
    memory_limit: int = 0
    
    # Network Metrics
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    network_rx_packets: int = 0
    network_tx_packets: int = 0
    network_rx_errors: int = 0
    network_tx_errors: int = 0
    
    # Filesystem Metrics
    fs_usage: int = 0
    fs_limit: int = 0
    fs_reads: int = 0
    fs_writes: int = 0
    fs_read_bytes: int = 0
    fs_write_bytes: int = 0
    
    # Process Metrics
    processes: int = 0
    threads: int = 0
    file_descriptors: int = 0

class PodMetricsCollector:
    """Coletor de métricas específicas para um pod"""
    
    def __init__(self, cadvisor_url: str = "http://localhost:8080", timeout: int = 30):
        self.cadvisor_url = cadvisor_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """Testa conexão com cAdvisor"""
        try:
            response = self.session.get(f"{self.cadvisor_url}/healthz")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Erro ao conectar com cAdvisor: {e}")
            return False
    
    def get_pod_metrics_from_prometheus(self, pod_name: str) -> List[PodMetrics]:
        """Coleta métricas do pod via endpoint Prometheus"""
        try:
            response = self.session.get(f"{self.cadvisor_url}/metrics")
            response.raise_for_status()
            
            metrics_text = response.text
            pod_metrics = []
            
            # Parse das métricas Prometheus
            metrics_data = self._parse_prometheus_metrics(metrics_text, pod_name)
            
            if metrics_data:
                # Agrupar por container
                containers = self._group_metrics_by_container(metrics_data, pod_name)
                
                for container_path, container_metrics in containers.items():
                    pod_metric = self._create_pod_metrics_from_prometheus(
                        container_metrics, pod_name, container_path
                    )
                    if pod_metric:
                        pod_metrics.append(pod_metric)
            
            return pod_metrics
            
        except Exception as e:
            self.logger.error(f"Erro ao obter métricas Prometheus: {e}")
            return []
    
    def get_pod_metrics_from_api(self, pod_name: str) -> List[PodMetrics]:
        """Coleta métricas do pod via API REST"""
        try:
            # Primeiro, obter lista de containers
            containers_response = self.session.get(f"{self.cadvisor_url}/api/v1.3/containers")
            containers_response.raise_for_status()
            containers_data = containers_response.json()
            
            pod_metrics = []
            
            # Procurar containers que pertencem ao pod
            for container_path, container_info in containers_data.items():
                if self._is_pod_container(container_info, pod_name):
                    # Obter estatísticas detalhadas do container
                    stats_response = self.session.get(
                        f"{self.cadvisor_url}/api/v1.3/containers{container_path}",
                        params={"num_stats": 1}
                    )
                    stats_response.raise_for_status()
                    stats_data = stats_response.json()
                    
                    # Processar estatísticas
                    for path, data in stats_data.items():
                        if 'stats' in data and data['stats']:
                            latest_stat = data['stats'][-1]  # Estatística mais recente
                            
                            pod_metric = self._create_pod_metrics_from_api(
                                data, latest_stat, pod_name
                            )
                            if pod_metric:
                                pod_metrics.append(pod_metric)
            
            return pod_metrics
            
        except Exception as e:
            self.logger.error(f"Erro ao obter métricas via API: {e}")
            return []
    
    def _parse_prometheus_metrics(self, metrics_text: str, pod_name: str) -> Dict[str, Any]:
        """Parse das métricas Prometheus filtradas por pod"""
        metrics_data = {}
        
        for line in metrics_text.split('\n'):
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            # Verificar se a linha contém o nome do pod
            if f'pod="{pod_name}"' not in line and f'pod_name="{pod_name}"' not in line:
                continue
            
            # Parse da métrica
            metric_info = self._parse_metric_line(line)
            if metric_info:
                metric_name = metric_info['metric_name']
                if metric_name not in metrics_data:
                    metrics_data[metric_name] = []
                metrics_data[metric_name].append(metric_info)
        
        return metrics_data
    
    def _parse_metric_line(self, line: str) -> Optional[Dict]:
        """Parse de uma linha de métrica Prometheus"""
        try:
            # Regex para métricas com labels
            pattern = r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\{([^}]*)\}\s+([^\s]+)(?:\s+(\d+))?$'
            match = re.match(pattern, line)
            
            if not match:
                # Métrica sem labels
                simple_pattern = r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+([^\s]+)(?:\s+(\d+))?$'
                simple_match = re.match(simple_pattern, line)
                if simple_match:
                    metric_name, value, timestamp = simple_match.groups()
                    labels = {}
                else:
                    return None
            else:
                metric_name, labels_str, value, timestamp = match.groups()
                labels = self._parse_labels(labels_str)
            
            # Converter valor
            try:
                value = float(value)
            except ValueError:
                return None
            
            # Timestamp
            if timestamp:
                timestamp = datetime.fromtimestamp(int(timestamp) / 1000)
            else:
                timestamp = datetime.now()
            
            return {
                'metric_name': metric_name,
                'value': value,
                'timestamp': timestamp,
                'labels': labels
            }
            
        except Exception as e:
            self.logger.debug(f"Erro ao fazer parse da linha: {line} - {e}")
            return None
    
    def _parse_labels(self, labels_str: str) -> Dict[str, str]:
        """Parse dos labels de uma métrica"""
        labels = {}
        label_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)="([^"]*)"'
        matches = re.findall(label_pattern, labels_str)
        
        for key, value in matches:
            labels[key] = value
        
        return labels
    
    def _group_metrics_by_container(self, metrics_data: Dict, pod_name: str) -> Dict[str, Dict]:
        """Agrupa métricas por container"""
        containers = {}
        
        for metric_name, metric_list in metrics_data.items():
            for metric in metric_list:
                labels = metric.get('labels', {})
                
                # Identificar container
                container_name = labels.get('name', labels.get('container', 'unknown'))
                container_id = labels.get('id', container_name)
                
                if container_id not in containers:
                    containers[container_id] = {
                        'container_name': container_name,
                        'pod_name': pod_name,
                        'namespace': labels.get('namespace', 'unknown'),
                        'metrics': {}
                    }
                
                containers[container_id]['metrics'][metric_name] = metric
        
        return containers
    
    def _create_pod_metrics_from_prometheus(self, container_data: Dict, 
                                          pod_name: str, container_path: str) -> Optional[PodMetrics]:
        """Cria objeto PodMetrics a partir de dados Prometheus"""
        try:
            metrics = container_data.get('metrics', {})
            
            pod_metric = PodMetrics(
                pod_name=pod_name,
                container_name=container_data.get('container_name', 'unknown'),
                namespace=container_data.get('namespace', 'unknown'),
                timestamp=datetime.now()
            )
            
            # CPU Metrics
            if 'container_cpu_usage_seconds_total' in metrics:
                pod_metric.cpu_usage_total = metrics['container_cpu_usage_seconds_total']['value']
            
            if 'container_cpu_user_seconds_total' in metrics:
                pod_metric.cpu_usage_user = metrics['container_cpu_user_seconds_total']['value']
            
            if 'container_cpu_system_seconds_total' in metrics:
                pod_metric.cpu_usage_system = metrics['container_cpu_system_seconds_total']['value']
            
            if 'container_cpu_cfs_throttled_seconds_total' in metrics:
                pod_metric.cpu_throttled_seconds = metrics['container_cpu_cfs_throttled_seconds_total']['value']
            
            if 'container_cpu_cfs_throttled_periods_total' in metrics:
                pod_metric.cpu_throttled_periods = int(metrics['container_cpu_cfs_throttled_periods_total']['value'])
            
            # Memory Metrics
            if 'container_memory_usage_bytes' in metrics:
                pod_metric.memory_usage = int(metrics['container_memory_usage_bytes']['value'])
            
            if 'container_memory_working_set_bytes' in metrics:
                pod_metric.memory_working_set = int(metrics['container_memory_working_set_bytes']['value'])
            
            if 'container_memory_rss' in metrics:
                pod_metric.memory_rss = int(metrics['container_memory_rss']['value'])
            
            if 'container_memory_cache' in metrics:
                pod_metric.memory_cache = int(metrics['container_memory_cache']['value'])
            
            if 'container_memory_swap' in metrics:
                pod_metric.memory_swap = int(metrics['container_memory_swap']['value'])
            
            if 'container_spec_memory_limit_bytes' in metrics:
                pod_metric.memory_limit = int(metrics['container_spec_memory_limit_bytes']['value'])
            
            # Network Metrics
            if 'container_network_receive_bytes_total' in metrics:
                pod_metric.network_rx_bytes = int(metrics['container_network_receive_bytes_total']['value'])
            
            if 'container_network_transmit_bytes_total' in metrics:
                pod_metric.network_tx_bytes = int(metrics['container_network_transmit_bytes_total']['value'])
            
            if 'container_network_receive_packets_total' in metrics:
                pod_metric.network_rx_packets = int(metrics['container_network_receive_packets_total']['value'])
            
            if 'container_network_transmit_packets_total' in metrics:
                pod_metric.network_tx_packets = int(metrics['container_network_transmit_packets_total']['value'])
            
            # Filesystem Metrics
            if 'container_fs_usage_bytes' in metrics:
                pod_metric.fs_usage = int(metrics['container_fs_usage_bytes']['value'])
            
            if 'container_fs_limit_bytes' in metrics:
                pod_metric.fs_limit = int(metrics['container_fs_limit_bytes']['value'])
            
            if 'container_fs_reads_total' in metrics:
                pod_metric.fs_reads = int(metrics['container_fs_reads_total']['value'])
            
            if 'container_fs_writes_total' in metrics:
                pod_metric.fs_writes = int(metrics['container_fs_writes_total']['value'])
            
            # Process Metrics
            if 'container_processes' in metrics:
                pod_metric.processes = int(metrics['container_processes']['value'])
            
            if 'container_threads' in metrics:
                pod_metric.threads = int(metrics['container_threads']['value'])
            
            if 'container_file_descriptors' in metrics:
                pod_metric.file_descriptors = int(metrics['container_file_descriptors']['value'])
            
            return pod_metric
            
        except Exception as e:
            self.logger.error(f"Erro ao criar PodMetrics: {e}")
            return None
    
    def _is_pod_container(self, container_info: Dict, pod_name: str) -> bool:
        """Verifica se o container pertence ao pod especificado"""
        spec = container_info.get('spec', {})
        labels = spec.get('labels', {})
        
        # Verificar diferentes formas de identificação do pod
        pod_labels = [
            labels.get('io.kubernetes.pod.name'),
            labels.get('pod_name'),
            labels.get('pod')
        ]
        
        return pod_name in pod_labels
    
    def _create_pod_metrics_from_api(self, container_data: Dict, 
                                   latest_stat: Dict, pod_name: str) -> Optional[PodMetrics]:
        """Cria objeto PodMetrics a partir de dados da API"""
        try:
            spec = container_data.get('spec', {})
            labels = spec.get('labels', {})
            
            pod_metric = PodMetrics(
                pod_name=pod_name,
                container_name=labels.get('io.kubernetes.container.name', 'unknown'),
                namespace=labels.get('io.kubernetes.pod.namespace', 'unknown'),
                timestamp=pd.to_datetime(latest_stat.get('timestamp', datetime.now()))
            )
            
            # CPU Metrics
            cpu = latest_stat.get('cpu', {})
            if cpu:
                usage = cpu.get('usage', {})
                pod_metric.cpu_usage_total = usage.get('total', 0)
                pod_metric.cpu_usage_user = usage.get('user', 0)
                pod_metric.cpu_usage_system = usage.get('system', 0)
                pod_metric.cpu_load_average = cpu.get('load_average', 0)
                
                # Calcular taxa de CPU (aproximada)
                if pod_metric.cpu_usage_total > 0:
                    pod_metric.cpu_usage_rate = pod_metric.cpu_usage_total / 1e9  # Converter para cores
            
            # Memory Metrics
            memory = latest_stat.get('memory', {})
            if memory:
                pod_metric.memory_usage = memory.get('usage', 0)
                pod_metric.memory_working_set = memory.get('working_set', 0)
                pod_metric.memory_rss = memory.get('rss', 0)
                pod_metric.memory_cache = memory.get('cache', 0)
                pod_metric.memory_swap = memory.get('swap', 0)
                pod_metric.memory_max_usage = memory.get('max_usage', 0)
            
            # Memory limit do spec
            memory_limit = spec.get('memory', {}).get('limit', 0)
            if memory_limit:
                pod_metric.memory_limit = memory_limit
            
            # Network Metrics
            network = latest_stat.get('network', {})
            if network:
                pod_metric.network_rx_bytes = network.get('rx_bytes', 0)
                pod_metric.network_tx_bytes = network.get('tx_bytes', 0)
                pod_metric.network_rx_packets = network.get('rx_packets', 0)
                pod_metric.network_tx_packets = network.get('tx_packets', 0)
                pod_metric.network_rx_errors = network.get('rx_errors', 0)
                pod_metric.network_tx_errors = network.get('tx_errors', 0)
            
            # Filesystem Metrics
            filesystem = latest_stat.get('filesystem', [])
            if filesystem:
                # Usar o primeiro filesystem ou somar todos
                fs = filesystem[0] if filesystem else {}
                pod_metric.fs_usage = fs.get('usage', 0)
                pod_metric.fs_limit = fs.get('limit', 0)
                pod_metric.fs_reads = fs.get('reads_completed', 0)
                pod_metric.fs_writes = fs.get('writes_completed', 0)
                pod_metric.fs_read_bytes = fs.get('read_bytes', 0)
                pod_metric.fs_write_bytes = fs.get('write_bytes', 0)
            
            # Process Metrics
            processes = latest_stat.get('processes', {})
            if processes:
                pod_metric.processes = processes.get('process_count', 0)
                pod_metric.threads = processes.get('thread_count', 0)
                pod_metric.file_descriptors = processes.get('fd_count', 0)
            
            return pod_metric
            
        except Exception as e:
            self.logger.error(f"Erro ao criar PodMetrics da API: {e}")
            return None
    
    def collect_pod_metrics(self, pod_name: str, method: str = "both") -> List[PodMetrics]:
        """Coleta métricas do pod usando método especificado"""
        metrics = []
        
        if method in ["both", "prometheus"]:
            self.logger.info(f"Coletando métricas via Prometheus para pod: {pod_name}")
            prometheus_metrics = self.get_pod_metrics_from_prometheus(pod_name)
            metrics.extend(prometheus_metrics)
        
        if method in ["both", "api"]:
            self.logger.info(f"Coletando métricas via API para pod: {pod_name}")
            api_metrics = self.get_pod_metrics_from_api(pod_name)
            metrics.extend(api_metrics)
        
        return metrics
    
    def metrics_to_dataframe(self, metrics: List[PodMetrics]) -> pd.DataFrame:
        """Converte lista de métricas para DataFrame"""
        if not metrics:
            return pd.DataFrame()
        
        data = []
        for metric in metrics:
            data.append({
                'pod_name': metric.pod_name,
                'container_name': metric.container_name,
                'namespace': metric.namespace,
                'timestamp': metric.timestamp,
                'cpu_usage_total': metric.cpu_usage_total,
                'cpu_usage_user': metric.cpu_usage_user,
                'cpu_usage_system': metric.cpu_usage_system,
                'cpu_usage_rate': metric.cpu_usage_rate,
                'cpu_load_average': metric.cpu_load_average,
                'cpu_throttled_seconds': metric.cpu_throttled_seconds,
                'cpu_throttled_periods': metric.cpu_throttled_periods,
                'memory_usage_bytes': metric.memory_usage,
                'memory_usage_mb': metric.memory_usage / (1024 * 1024) if metric.memory_usage else 0,
                'memory_working_set_bytes': metric.memory_working_set,
                'memory_working_set_mb': metric.memory_working_set / (1024 * 1024) if metric.memory_working_set else 0,
                'memory_rss_bytes': metric.memory_rss,
                'memory_cache_bytes': metric.memory_cache,
                'memory_swap_bytes': metric.memory_swap,
                'memory_max_usage_bytes': metric.memory_max_usage,
                'memory_limit_bytes': metric.memory_limit,
                'memory_utilization_pct': (metric.memory_usage / metric.memory_limit * 100) if metric.memory_limit else 0,
                'network_rx_bytes': metric.network_rx_bytes,
                'network_tx_bytes': metric.network_tx_bytes,
                'network_rx_mb': metric.network_rx_bytes / (1024 * 1024) if metric.network_rx_bytes else 0,
                'network_tx_mb': metric.network_tx_bytes / (1024 * 1024) if metric.network_tx_bytes else 0,
                'network_rx_packets': metric.network_rx_packets,
                'network_tx_packets': metric.network_tx_packets,
                'network_rx_errors': metric.network_rx_errors,
                'network_tx_errors': metric.network_tx_errors,
                'fs_usage_bytes': metric.fs_usage,
                'fs_usage_mb': metric.fs_usage / (1024 * 1024) if metric.fs_usage else 0,
                'fs_limit_bytes': metric.fs_limit,
                'fs_utilization_pct': (metric.fs_usage / metric.fs_limit * 100) if metric.fs_limit else 0,
                'fs_reads': metric.fs_reads,
                'fs_writes': metric.fs_writes,
                'fs_read_bytes': metric.fs_read_bytes,
                'fs_write_bytes': metric.fs_write_bytes,
                'processes': metric.processes,
                'threads': metric.threads,
                'file_descriptors': metric.file_descriptors
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def print_metrics_summary(self, metrics: List[PodMetrics]) -> None:
        """Imprime resumo das métricas coletadas"""
        if not metrics:
            print("❌ Nenhuma métrica encontrada")
            return
        
        print(f"\n📊 Resumo das Métricas - Pod: {metrics[0].pod_name}")
        print("=" * 60)
        
        for i, metric in enumerate(metrics):
            print(f"\n🔹 Container {i+1}: {metric.container_name}")
            print(f"   Namespace: {metric.namespace}")
            print(f"   Timestamp: {metric.timestamp}")
            
            print(f"\n   💻 CPU:")
            print(f"     - Uso Total: {metric.cpu_usage_total/1e9:.4f} cores")
            print(f"     - Uso User: {metric.cpu_usage_user/1e9:.4f} cores")
            print(f"     - Uso System: {metric.cpu_usage_system/1e9:.4f} cores")
            print(f"     - Load Average: {metric.cpu_load_average:.2f}")
            if metric.cpu_throttled_seconds > 0:
                print(f"     - Throttled: {metric.cpu_throttled_seconds:.2f}s ({metric.cpu_throttled_periods} períodos)")
            
            print(f"\n   🧠 Memória:")
            print(f"     - Uso: {metric.memory_usage / (1024*1024):.2f} MB")
            print(f"     - Working Set: {metric.memory_working_set / (1024*1024):.2f} MB")
            print(f"     - RSS: {metric.memory_rss / (1024*1024):.2f} MB")
            print(f"     - Cache: {metric.memory_cache / (1024*1024):.2f} MB")
            if metric.memory_limit > 0:
                utilization = (metric.memory_usage / metric.memory_limit) * 100
                print(f"     - Limite: {metric.memory_limit / (1024*1024):.2f} MB")
                print(f"     - Utilização: {utilization:.2f}%")
            
            print(f"\n   🌐 Rede:")
            print(f"     - RX: {metric.network_rx_bytes / (1024*1024):.2f} MB ({metric.network_rx_packets} pacotes)")
            print(f"     - TX: {metric.network_tx_bytes / (1024*1024):.2f} MB ({metric.network_tx_packets} pacotes)")
            if metric.network_rx_errors > 0 or metric.network_tx_errors > 0:
                print(f"     - Erros: RX={metric.network_rx_errors}, TX={metric.network_tx_errors}")
            
            print(f"\n   💾 Filesystem:")
            print(f"     - Uso: {metric.fs_usage / (1024*1024):.2f} MB")
            if metric.fs_limit > 0:
                fs_utilization = (metric.fs_usage / metric.fs_limit) * 100
                print(f"     - Limite: {metric.fs_limit / (1024*1024):.2f} MB")
                print(f"     - Utilização: {fs_utilization:.2f}%")
            print(f"     - Operações: {metric.fs_reads} leituras, {metric.fs_writes} escritas")
            
            print(f"\n   🔧 Processos:")
            print(f"     - Processos: {metric.processes}")
            print(f"     - Threads: {metric.threads}")
            print(f"     - File Descriptors: {metric.file_descriptors}")

def main():
    parser = argparse.ArgumentParser(
        description="Coletor de métricas específicas de pod do cAdvisor"
    )
    
    parser.add_argument(
        "pod_name",
        help="Nome do pod para coletar métricas"
    )
    
    parser.add_argument(
        "--cadvisor-url",
        default="http://localhost:8080",
        help="URL do cAdvisor (default: http://localhost:8080)"
    )
    
    parser.add_argument(
        "--method",
        choices=["prometheus", "api", "both"],
        default="both",
        help="Método de coleta (default: both)"
    )
    
    parser.add_argument(
        "--output",
        help="Arquivo de saída (CSV)"
    )
    
    parser.add_argument(
        "--format",
        choices=["csv", "json", "excel"],
        default="csv",
        help="Formato de saída (default: csv)"
    )
    
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Coleta contínua (pressione Ctrl+C para parar)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Intervalo de coleta em segundos para modo contínuo (default: 30)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Modo verboso"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Criar coletor
    collector = PodMetricsCollector(args.cadvisor_url)
    
    # Testar conexão
    print(f"🔗 Testando conexão com cAdvisor em {args.cadvisor_url}...")
    if not collector.test_connection():
        print("❌ Erro: Não foi possível conectar ao cAdvisor")
        print("Verifique se o cAdvisor está rodando e acessível")
        sys.exit(1)
    
    print("✅ Conexão estabelecida com sucesso!")
    
    try:
        if args.continuous:
            print(f"🔄 Iniciando coleta contínua para pod '{args.pod_name}' (intervalo: {args.interval}s)")
            print("Pressione Ctrl+C para parar...")
            
            all_metrics = []
            
            while True:
                print(f"\n📊 Coletando métricas... ({datetime.now().strftime('%H:%M:%S')})")
                
                metrics = collector.collect_pod_metrics(args.pod_name, args.method)
                
                if metrics:
                    all_metrics.extend(metrics)
                    collector.print_metrics_summary(metrics)
                else:
                    print(f"⚠️  Nenhuma métrica encontrada para o pod '{args.pod_name}'")
                
                time.sleep(args.interval)
        
        else:
            print(f"📊 Coletando métricas do pod '{args.pod_name}'...")
            
            metrics = collector.collect_pod_metrics(args.pod_name, args.method)
            
            if not metrics:
                print(f"❌ Nenhuma métrica encontrada para o pod '{args.pod_name}'")
                print("\nVerifique se:")
                print("- O nome do pod está correto")
                print("- O pod está rodando")
                print("- O cAdvisor tem acesso ao pod")
                sys.exit(1)
            
            all_metrics = metrics
    
    except KeyboardInterrupt:
        print("\n⏹️  Coleta interrompida pelo usuário")
        if 'all_metrics' not in locals():
            all_metrics = []
    
    # Processar e salvar resultados
    if all_metrics:
        print(f"\n📈 Processando {len(all_metrics)} métricas coletadas...")
        
        # Mostrar resumo
        collector.print_metrics_summary(all_metrics[-len(metrics):] if args.continuous else all_metrics)
        
        # Converter para DataFrame
        df = collector.metrics_to_dataframe(all_metrics)
        
        if not df.empty:
            print(f"\n📊 DataFrame criado com {len(df)} registros e {len(df.columns)} colunas")
            
            # Salvar arquivo se especificado
            if args.output:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                if args.format == "csv":
                    filename = args.output if args.output.endswith('.csv') else f"{args.output}.csv"
                    df.to_csv(filename, index=False)
                    print(f"💾 Dados salvos em: {filename}")
                
                elif args.format == "json":
                    filename = args.output if args.output.endswith('.json') else f"{args.output}.json"
                    df.to_json(filename, orient='records', date_format='iso', indent=2)
                    print(f"💾 Dados salvos em: {filename}")
                
                elif args.format == "excel":
                    filename = args.output if args.output.endswith('.xlsx') else f"{args.output}.xlsx"
                    df.to_excel(filename, index=False)
                    print(f"💾 Dados salvos em: {filename}")
            
            # Mostrar estatísticas finais
            print(f"\n📈 Estatísticas Finais:")
            print(f"- Período: {df['timestamp'].min()} até {df['timestamp'].max()}")
            print(f"- Containers únicos: {df['container_name'].nunique()}")
            
            if 'memory_usage_mb' in df.columns:
                print(f"- Uso médio de memória: {df['memory_usage_mb'].mean():.2f} MB")
                print(f"- Pico de memória: {df['memory_usage_mb'].max():.2f} MB")
            
            if 'cpu_usage_rate' in df.columns:
                print(f"- Uso médio de CPU: {df['cpu_usage_rate'].mean():.4f} cores")
                print(f"- Pico de CPU: {df['cpu_usage_rate'].max():.4f} cores")
        
        else:
            print("⚠️  DataFrame vazio - nenhum dado para salvar")
    
    else:
        print("❌ Nenhuma métrica foi coletada")

if __name__ == "__main__":
    main()