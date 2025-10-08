"""
Sistema de Coleta de Métricas para ML - Detecção de Sobrecarga em Kubernetes
Autor: Sistema de Monitoramento
Descrição: Coleta métricas do cAdvisor e gera dataset estruturado para Machine Learning
          com thresholds configuráveis para definição de sobrecarga
Versão: 2.0 - Com correção de queries Prometheus e thresholds parametrizados
"""


import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta
import json
import logging
import argparse
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ThresholdConfig:
    """Classe para gerenciar configurações de thresholds"""
    
    def __init__(self, 
                 memory_warning: float = 30.0,
                 memory_overload: float = 40.0, 
                 memory_critical: float = 50.0,
                 cpu_warning: float = 70.0,
                 cpu_overload: float = 80.0,
                 cpu_critical: float = 90.0,
                 disk_warning: float = 75.0,
                 disk_overload: float = 85.0,
                 disk_critical: float = 95.0):
        """
        Inicializa configuração de thresholds
        
        Args:
            memory_warning: Threshold de warning para memória (%)
            memory_overload: Threshold de sobrecarga para memória (%)
            memory_critical: Threshold crítico para memória (%)
            cpu_warning: Threshold de warning para CPU (%)
            cpu_overload: Threshold de sobrecarga para CPU (%)
            cpu_critical: Threshold crítico para CPU (%)
            disk_warning: Threshold de warning para disco (%)
            disk_overload: Threshold de sobrecarga para disco (%)
            disk_critical: Threshold crítico para disco (%)
        """
        # Validação
        self._validate_threshold(memory_warning, memory_overload, memory_critical, "Memory")
        self._validate_threshold(cpu_warning, cpu_overload, cpu_critical, "CPU")
        self._validate_threshold(disk_warning, disk_overload, disk_critical, "Disk")
        
        # Memória
        self.memory_warning = memory_warning
        self.memory_overload = memory_overload
        self.memory_critical = memory_critical
        
        # CPU
        self.cpu_warning = cpu_warning
        self.cpu_overload = cpu_overload
        self.cpu_critical = cpu_critical
        
        # Disco
        self.disk_warning = disk_warning
        self.disk_overload = disk_overload
        self.disk_critical = disk_critical
        
        logger.info("📊 Thresholds configurados:")
        logger.info(f"   Memory: Warning={memory_warning}%, Overload={memory_overload}%, Critical={memory_critical}%")
        logger.info(f"   CPU: Warning={cpu_warning}%, Overload={cpu_overload}%, Critical={cpu_critical}%")
        logger.info(f"   Disk: Warning={disk_warning}%, Overload={disk_overload}%, Critical={disk_critical}%")
    
    def _validate_threshold(self, warning: float, overload: float, critical: float, name: str):
        """Valida se os thresholds estão em ordem crescente"""
        if not (0 <= warning < overload < critical <= 100):
            raise ValueError(
                f"Thresholds de {name} inválidos! "
                f"Devem estar entre 0-100 e em ordem: warning < overload < critical. "
                f"Valores fornecidos: warning={warning}, overload={overload}, critical={critical}"
            )
    
    def to_dict(self) -> Dict:
        """Retorna thresholds como dicionário"""
        return {
            'memory': {
                'warning': self.memory_warning,
                'overload': self.memory_overload,
                'critical': self.memory_critical
            },
            'cpu': {
                'warning': self.cpu_warning,
                'overload': self.cpu_overload,
                'critical': self.cpu_critical
            },
            'disk': {
                'warning': self.disk_warning,
                'overload': self.disk_overload,
                'critical': self.disk_critical
            }
        }
    
    def save_to_file(self, filepath: str = 'thresholds_config.json'):
        """Salva configuração em arquivo JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"💾 Thresholds salvos em: {filepath}")
    
    @classmethod
    def load_from_file(cls, filepath: str = 'thresholds_config.json'):
        """Carrega configuração de arquivo JSON"""
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        return cls(
            memory_warning=config['memory']['warning'],
            memory_overload=config['memory']['overload'],
            memory_critical=config['memory']['critical'],
            cpu_warning=config['cpu']['warning'],
            cpu_overload=config['cpu']['overload'],
            cpu_critical=config['cpu']['critical'],
            disk_warning=config['disk']['warning'],
            disk_overload=config['disk']['overload'],
            disk_critical=config['disk']['critical']
        )


class PrometheusConnector:
    """Classe para conexão e queries no Prometheus"""
    
    def __init__(self, prometheus_url: str, timeout: int = 60, 
                 username: Optional[str] = None, password: Optional[str] = None,
                 verify_ssl: bool = True):
        """
        Inicializa connector do Prometheus
        
        Args:
            prometheus_url: URL do Prometheus
            timeout: Timeout para requisições em segundos
            username: Usuário para Basic Auth (opcional)
            password: Senha para Basic Auth (opcional)
            verify_ssl: Verificar certificado SSL (default: True)
        """
        self.prometheus_url = prometheus_url.rstrip('/')
        self.api_url = f"{self.prometheus_url}/api/v1"
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Configurar autenticação
        self.auth = None
        if username and password:
            self.auth = (username, password)
            logger.info(f"Prometheus Connector iniciado com Basic Auth: {prometheus_url} (usuário: {username})")
        else:
            logger.info(f"Prometheus Connector iniciado sem autenticação: {self.prometheus_url}")
        
        if not verify_ssl:
            logger.warning("⚠️  Verificação SSL desabilitada!")
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def test_connection(self) -> bool:
        """Testa conexão com Prometheus"""
        try:
            response = requests.get(
                f"{self.api_url}/query", 
                params={'query': 'up'}, 
                timeout=10,
                auth=self.auth,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            logger.info("✅ Conexão com Prometheus estabelecida")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("❌ Erro de autenticação (401): Credenciais inválidas")
            elif e.response.status_code == 403:
                logger.error("❌ Erro de autorização (403): Sem permissão")
            else:
                logger.error(f"❌ Erro HTTP ao conectar com Prometheus: {e}")
            return False
        except requests.exceptions.SSLError as e:
            logger.error(f"❌ Erro SSL: {e}")
            logger.error("   Dica: Use --no-verify-ssl para ignorar certificado inválido")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com Prometheus: {e}")
            return False
    
    def query_range(self, query: str, start: int, end: int, step: str = '30s') -> Optional[Dict]:
        """Executa query com range temporal"""
        try:
            response = requests.get(
                f"{self.api_url}/query_range",
                params={'query': query, 'start': start, 'end': end, 'step': step},
                timeout=self.timeout,
                auth=self.auth,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(f"❌ Erro de autenticação na query: {query[:50]}...")
            else:
                logger.error(f"Erro HTTP ao executar query: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            return None
    
    def query_instant(self, query: str) -> Optional[Dict]:
        """Executa query instantânea"""
        try:
            response = requests.get(
                f"{self.api_url}/query",
                params={'query': query},
                timeout=self.timeout,
                auth=self.auth,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(f"❌ Erro de autenticação na query instantânea")
            else:
                logger.error(f"Erro HTTP ao executar query instantânea: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao executar query instantânea: {e}")
            return None


class MetricsExtractor:
    """Classe para extração de métricas do cAdvisor"""
    
    def __init__(self, connector: PrometheusConnector):
        self.connector = connector
        self.raw_metrics = []




    def get_metrics_config(self) -> Dict[str, str]:
        """Retorna configuração de métricas a serem coletadas"""
        return {
            # Métricas de CPU
            'cpu_usage_total': 'rate(container_cpu_usage_seconds_total[5m])',
            'cpu_user': 'rate(container_cpu_user_seconds_total[5m])',
            'cpu_system': 'rate(container_cpu_system_seconds_total[5m])',
            'cpu_throttled_periods': 'rate(container_cpu_cfs_throttled_periods_total[5m])',
            'cpu_throttled_time': 'rate(container_cpu_cfs_throttled_seconds_total[5m])',
            
            # Métricas de Memória
            'memory_usage_bytes': 'container_memory_usage_bytes',
            'memory_working_set_bytes': 'container_memory_working_set_bytes',
            'memory_rss': 'container_memory_rss',
            'memory_cache': 'container_memory_cache',
            'memory_swap': 'container_memory_swap',
            'memory_max_usage': 'container_memory_max_usage_bytes',
            'memory_failures': 'rate(container_memory_failures_total[5m])',
            
            # Limites e Especificações
            #  'memory_limit': 'container_spec_memory_limit_bytes', 
              'memory_limit': 'kube_pod_container_resource_limits',

            'cpu_quota': 'container_spec_cpu_quota',
            'cpu_period': 'container_spec_cpu_period',
            
            # Métricas de Rede
            'network_rx_bytes': 'rate(container_network_receive_bytes_total[5m])',
            'network_tx_bytes': 'rate(container_network_transmit_bytes_total[5m])',
            'network_rx_errors': 'rate(container_network_receive_errors_total[5m])',
            'network_tx_errors': 'rate(container_network_transmit_errors_total[5m])',
            'network_rx_packets_dropped': 'rate(container_network_receive_packets_dropped_total[5m])',
            'network_tx_packets_dropped': 'rate(container_network_transmit_packets_dropped_total[5m])',
            
            # Métricas de Disco
            'fs_usage_bytes': 'container_fs_usage_bytes',
            'fs_limit_bytes': 'container_fs_limit_bytes',
            'fs_reads': 'rate(container_fs_reads_bytes_total[5m])',
            'fs_writes': 'rate(container_fs_writes_bytes_total[5m])',
            'fs_read_time': 'rate(container_fs_read_seconds_total[5m])',
            'fs_write_time': 'rate(container_fs_write_seconds_total[5m])',
            
            # Processos e Threads
            'processes': 'container_processes',
            'threads': 'container_threads',
            'file_descriptors': 'container_file_descriptors',
            'sockets': 'container_sockets',
            
            # === NOVAS MÉTRICAS DE ESTADO DO POD ===
            
            # Estado e Disponibilidade do Pod
            'pod_ready': 'kube_pod_status_ready',
            'pod_phase': 'kube_pod_status_phase',
            'pod_conditions': 'kube_pod_status_condition',
            'pod_scheduled': 'kube_pod_status_scheduled',
            
            # Restarts e Falhas
            'container_restarts': 'kube_pod_container_status_restarts_total',
            'container_ready': 'kube_pod_container_status_ready',
            'container_running': 'kube_pod_container_status_running',
            'container_waiting': 'kube_pod_container_status_waiting',
            'container_terminated': 'kube_pod_container_status_terminated',
            
            # OOM e Problemas de Memória
            'oom_kills': 'container_oom_events_total',
            'oom_kill_rate': 'rate(container_oom_events_total[5m])',
            
            # Latência e Performance de Rede
            'network_tcp_connections': 'container_network_tcp_usage_total',
            'network_udp_connections': 'container_network_udp_usage_total',
            
            # Age e Uptime
            'pod_start_time': 'kube_pod_start_time',
            'pod_created': 'kube_pod_created',
            'container_start_time': 'container_start_time_seconds',
            
            # Labels e Metadata que podem indicar degradação
            'pod_labels': 'kube_pod_labels',
            'pod_owner': 'kube_pod_owner',
            
            # Métricas de Probe (Liveness/Readiness)
            'probe_success': 'prober_probe_total',
            
            # QoS Class (pode afetar scheduling e eviction)
            'pod_qos_class': 'kube_pod_status_qos_class',
            
            # Resource Requests vs Limits (útil para detectar overcommit)
            'memory_requests': 'kube_pod_container_resource_requests',
            'memory_limits': 'kube_pod_container_resource_limits',
            'cpu_requests': 'kube_pod_container_resource_requests',
            'cpu_limits': 'kube_pod_container_resource_limits',
            
            # Eviction e Preemption
            'pod_deletion_timestamp': 'kube_pod_deletion_timestamp',
            
            # Métricas de I/O que podem indicar degradação
            'io_service_bytes_read': 'rate(container_fs_io_current[5m])',
            'io_service_bytes_write': 'rate(container_fs_io_current[5m])',
            
            # Context Switches (alto número pode indicar problemas)
            'cpu_context_switches': 'rate(container_cpu_cfs_periods_total[5m])',
            
            # Tasks State (podem indicar problemas de scheduling)
            'tasks_sleeping': 'container_tasks_state',
            'tasks_running': 'container_tasks_state',
            'tasks_stopped': 'container_tasks_state',
            'tasks_uninterruptible': 'container_tasks_state',
            
            # Latência de Startup (container pode estar demorando a iniciar)
            'container_last_seen': 'container_last_seen',
            
            # Métricas de Node que afetam o Pod
            'node_memory_pressure': 'kube_node_status_condition',
            'node_disk_pressure': 'kube_node_status_condition',
            'node_pid_pressure': 'kube_node_status_condition',
            'node_ready': 'kube_node_status_condition',
        }
    
    def extract_metrics(self, start_time: datetime, end_time: datetime, 
                       step: str = '30s', pod_filter: Optional[str] = None,
                       namespace: Optional[str] = None) -> pd.DataFrame:
        """
        Extrai métricas do cAdvisor para o período especificado
        
        Args:
            start_time: Data/hora inicial
            end_time: Data/hora final
            step: Intervalo entre medições
            pod_filter: Filtro regex para pods
            namespace: Namespace específico
        
        Returns:
            DataFrame com métricas brutas
        """
        logger.info(f"Iniciando extração de métricas: {start_time} até {end_time}")
        
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())
        
        metrics_config = self.get_metrics_config()
        all_data = []

        

        metricas = []
        for metric_name, metric_query in metrics_config.items():
            # Adiciona filtros
            filters = ['container!="POD"', 'container!=""']
            if metric_name == 'memory_limit':
                filters.append(f'resource="memory"')
            if pod_filter:
                filters.append(f'pod=~"{pod_filter}"')
            if namespace:
                filters.append(f'namespace="{namespace}"')
            
            # Monta query corretamente baseado no tipo de métrica
            filters_str = ','.join(filters)
            
            # Se a métrica usa rate(), os filtros vão DENTRO do rate()
            if metric_query.startswith('rate('):
                # Extrai o nome da métrica e o intervalo
                # Ex: rate(container_cpu_usage_seconds_total[5m])
                metric_base = metric_query.replace('rate(', '').replace(')', '')
                metric_name_part = metric_base.split('[')[0]
                interval_part = '[' + metric_base.split('[')[1]
                
                # Reconstroi com filtros corretos
                query = f'rate({metric_name_part}{{{filters_str}}}{interval_part})'
            else:
                # Métricas sem rate() mantém sintaxe original
                query = f'{metric_query}{{{filters_str}}}'
            
               # Armazena no dicionário
            metricas.append({'metric_name':metric_name, 'metric_query':query})
 

            logger.info(f"Coletando: {metric_name}")
            logger.debug(f"Query: {query}")
            result = self.connector.query_range(query, start_ts, end_ts, step)
            
            if result and result['status'] == 'success':
                for item in result['data']['result']:
                    for timestamp, value in item['values']:
                        record = {
                            'timestamp': datetime.fromtimestamp(timestamp),
                            'metric_name': metric_name,
                            'value': float(value) if value != 'NaN' else np.nan,
                            'pod': item['metric'].get('pod', ''),
                            'container': item['metric'].get('container', ''),
                            'namespace': item['metric'].get('namespace', ''),
                            'node': item['metric'].get('node', ''),
                        }
                        all_data.append(record)
        
        #gera arquivo com as métricas utilizadas   
        df_metricas = pd.DataFrame(metricas)
        df_metricas.index.name = 'metric_id'
        df_metricas.to_csv('metricas_utilizadas.csv', index=True)
        
        df = pd.DataFrame(all_data)
        logger.info(f"✅ Extração concluída: {len(df)} registros coletados")
        return df


class FeatureEngineer:
    """Classe para engenharia de features para ML"""
    
    def __init__(self, thresholds: ThresholdConfig):
        self.thresholds = thresholds
        self.feature_columns = []
    
    def create_ml_features(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma métricas brutas em features para ML
        
        Args:
            df_raw: DataFrame com métricas brutas
        
        Returns:
            DataFrame com features estruturadas
        """
        logger.info("Iniciando engenharia de features...")
        
        # Pivot para ter uma linha por timestamp/pod/container
        df_pivot = df_raw.pivot_table(
            index=['timestamp', 'pod', 'container', 'namespace', 'node'],
            columns='metric_name',
            values='value',
            aggfunc='first'
        ).reset_index()
        
        # Remove colunas completamente vazias
        df_pivot = df_pivot.dropna(axis=1, how='all')
        
        logger.info(f"Features base criadas: {df_pivot.shape}")
        
        # Calcula features derivadas
        df_features = self._calculate_derived_features(df_pivot)
        
        # Adiciona features temporais
        df_features = self._add_temporal_features(df_features)
        
        # Adiciona features estatísticas (rolling)
        df_features = self._add_statistical_features(df_features)
        
        # Cria labels para ML (target) - USA THRESHOLDS CONFIGURÁVEIS
        df_features = self._create_target_labels(df_features)
        
        logger.info(f"✅ Features finais: {df_features.shape}")
        logger.info(f"Colunas: {list(df_features.columns)}")
        
        return df_features
    
    def _calculate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula features derivadas das métricas base"""
        logger.info("Calculando features derivadas...")
        
        # Percentual de uso de memória
        if 'memory_working_set_bytes' in df.columns and 'memory_limit' in df.columns:
            df['memory_usage_percent'] = (df['memory_working_set_bytes'] / df['memory_limit']) * 100
            df['memory_usage_percent'] = df['memory_usage_percent'].clip(0, 100)
        
        # Percentual de uso de CPU (baseado em quota)
        if 'cpu_usage_total' in df.columns and 'cpu_quota' in df.columns and 'cpu_period' in df.columns:
            cpu_limit_cores = (df['cpu_quota'] / df['cpu_period'])
            df['cpu_usage_percent'] = (df['cpu_usage_total'] / cpu_limit_cores) * 100
            df['cpu_usage_percent'] = df['cpu_usage_percent'].clip(0, 200)
        
        # Percentual de uso de disco
        if 'fs_usage_bytes' in df.columns and 'fs_limit_bytes' in df.columns:
            df['disk_usage_percent'] = (df['fs_usage_bytes'] / df['fs_limit_bytes']) * 100
            df['disk_usage_percent'] = df['disk_usage_percent'].clip(0, 100)
        
        # Taxa de throttling de CPU
        if 'cpu_throttled_periods' in df.columns and 'cpu_throttled_time' in df.columns:
            df['cpu_throttling_rate'] = df['cpu_throttled_time'] / (df['cpu_throttled_periods'] + 0.001)
        
        # Uso de memória vs cache
        if 'memory_rss' in df.columns and 'memory_cache' in df.columns:
            df['memory_rss_percent'] = df['memory_rss'] / (df['memory_usage_bytes'] + 1)
            df['memory_cache_percent'] = df['memory_cache'] / (df['memory_usage_bytes'] + 1)
        
        # Taxa de rede total
        if 'network_rx_bytes' in df.columns and 'network_tx_bytes' in df.columns:
            df['network_total_bytes'] = df['network_rx_bytes'] + df['network_tx_bytes']
        
        # Taxa de IO de disco
        if 'fs_reads' in df.columns and 'fs_writes' in df.columns:
            df['disk_io_total'] = df['fs_reads'] + df['fs_writes']
        
        # Densidade de processos/threads
        if 'processes' in df.columns and 'threads' in df.columns:
            df['threads_per_process'] = df['threads'] / (df['processes'] + 1)
        
        # === NOVAS FEATURES PARA DETECÇÃO DE DEGRADAÇÃO ===
        
        # Taxa de erros de rede (indicador de problemas)
        if 'network_rx_errors' in df.columns and 'network_tx_errors' in df.columns:
            df['network_error_rate'] = df['network_rx_errors'] + df['network_tx_errors']
            
            # Proporção de erros vs tráfego total
            if 'network_total_bytes' in df.columns:
                df['network_error_ratio'] = df['network_error_rate'] / (df['network_total_bytes'] + 1)
        
        # Taxa de pacotes dropados (sinal de saturação)
        if 'network_rx_packets_dropped' in df.columns and 'network_tx_packets_dropped' in df.columns:
            df['network_packets_dropped_total'] = df['network_rx_packets_dropped'] + df['network_tx_packets_dropped']
        
        # Latência de I/O (tempo por operação)
        if 'fs_read_time' in df.columns and 'fs_reads' in df.columns:
            df['fs_read_latency'] = df['fs_read_time'] / (df['fs_reads'] + 0.001)
        
        if 'fs_write_time' in df.columns and 'fs_writes' in df.columns:
            df['fs_write_latency'] = df['fs_write_time'] / (df['fs_writes'] + 0.001)
        
        # Uso de file descriptors (pode indicar leak)
        if 'file_descriptors' in df.columns and 'processes' in df.columns:
            df['fd_per_process'] = df['file_descriptors'] / (df['processes'] + 1)
        
        # Taxa de OOM kills (problema crítico)
        if 'oom_kill_rate' in df.columns:
            df['has_oom_kills'] = (df['oom_kill_rate'] > 0).astype(int)
        
        # Container restart indicator (sinal de instabilidade)
        if 'container_restarts' in df.columns:
            df['has_restarts'] = (df['container_restarts'] > 0).astype(int)
            # Taxa de restarts (diferença entre períodos)
            df['restart_rate'] = df.groupby(['pod', 'container'])['container_restarts'].diff().fillna(0)
        
        # Pod age (tempo desde início - pode correlacionar com degradação)
        if 'pod_start_time' in df.columns:
            current_time = pd.Timestamp.now().timestamp()
            df['pod_age_seconds'] = current_time - df['pod_start_time']
            df['pod_age_hours'] = df['pod_age_seconds'] / 3600
        
        # Memory pressure indicator
        if 'memory_working_set_bytes' in df.columns and 'memory_limit' in df.columns:
            # Distância da memória ao limite
            df['memory_headroom_bytes'] = df['memory_limit'] - df['memory_working_set_bytes']
            df['memory_headroom_percent'] = (df['memory_headroom_bytes'] / df['memory_limit']) * 100
            
            # Indicador de pressão de memória
            df['memory_pressure'] = (df['memory_usage_percent'] > 80).astype(int)
        
        # CPU saturation indicator
        if 'cpu_throttled_periods' in df.columns:
            df['cpu_saturated'] = (df['cpu_throttled_periods'] > 0).astype(int)
        
        # I/O wait indicator (tasks uninterruptible = waiting for I/O)
        if 'tasks_uninterruptible' in df.columns and 'processes' in df.columns:
            df['io_wait_ratio'] = df['tasks_uninterruptible'] / (df['processes'] + 1)
        
        # Resource overcommit ratio
        if 'memory_requests' in df.columns and 'memory_limits' in df.columns:
            df['memory_overcommit_ratio'] = df['memory_limits'] / (df['memory_requests'] + 1)
        
        if 'cpu_requests' in df.columns and 'cpu_limits' in df.columns:
            df['cpu_overcommit_ratio'] = df['cpu_limits'] / (df['cpu_requests'] + 1)
        
        # Stability score (combinação de múltiplos indicadores)
        stability_factors = []
        
        if 'has_restarts' in df.columns:
            stability_factors.append(df['has_restarts'])
        
        if 'has_oom_kills' in df.columns:
            stability_factors.append(df['has_oom_kills'])
        
        if 'memory_pressure' in df.columns:
            stability_factors.append(df['memory_pressure'])
        
        if 'cpu_saturated' in df.columns:
            stability_factors.append(df['cpu_saturated'])
        
        if stability_factors:
            # Score de 0 (estável) a N (instável)
            df['instability_score'] = sum(stability_factors)
            
            # Binário: instável se algum fator estiver ativo
            df['is_unstable'] = (df['instability_score'] > 0).astype(int)
        
        # Network health score
        network_health_factors = []
        
        if 'network_error_rate' in df.columns:
            network_health_factors.append((df['network_error_rate'] > 0).astype(int))
        
        if 'network_packets_dropped_total' in df.columns:
            network_health_factors.append((df['network_packets_dropped_total'] > 0).astype(int))
        
        if network_health_factors:
            df['network_unhealthy'] = sum(network_health_factors)
            df['has_network_issues'] = (df['network_unhealthy'] > 0).astype(int)
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona features temporais"""
        logger.info("Adicionando features temporais...")
        
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['minute'] = df['timestamp'].dt.minute
        
        # Períodos do dia
        df['period'] = pd.cut(df['hour'], 
                             bins=[0, 6, 12, 18, 24], 
                             labels=['madrugada', 'manha', 'tarde', 'noite'],
                             include_lowest=True)
        
        # Fim de semana
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        return df
    
    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona features estatísticas (rolling windows)"""
        logger.info("Adicionando features estatísticas...")
        
        # Ordena por pod/container e timestamp
        df = df.sort_values(['pod', 'container', 'timestamp'])
        
        # Métricas numéricas para calcular estatísticas
        numeric_metrics = ['memory_usage_percent', 'cpu_usage_percent', 
                          'disk_usage_percent', 'network_total_bytes']
        
        for metric in numeric_metrics:
            if metric in df.columns:
                # Agrupa por pod/container
                grouped = df.groupby(['pod', 'container'])[metric]
                
                # Rolling mean (5 períodos)
                df[f'{metric}_rolling_mean_5'] = grouped.transform(
                    lambda x: x.rolling(window=5, min_periods=1).mean()
                )
                
                # Rolling std (5 períodos)
                df[f'{metric}_rolling_std_5'] = grouped.transform(
                    lambda x: x.rolling(window=5, min_periods=1).std()
                )
                
                # Diferença com período anterior
                df[f'{metric}_diff'] = grouped.diff()
                
                # Taxa de mudança
                df[f'{metric}_pct_change'] = grouped.pct_change().fillna(0)
        
        return df
    
    def _create_target_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cria labels (targets) para treinamento de ML usando thresholds configuráveis
        
        Labels criadas:
        - memory_overload: 1 se memória > threshold_overload, 0 caso contrário
        - cpu_overload: 1 se CPU > threshold_overload, 0 caso contrário
        - disk_overload: 1 se disco > threshold_overload, 0 caso contrário
        - memory_critical: 1 se memória > threshold_critical
        - cpu_critical: 1 se CPU > threshold_critical
        - disk_critical: 1 se disco > threshold_critical
        - critical_overload: 1 se qualquer recurso está crítico
        - overload_severity: 0 (normal), 1 (warning), 2 (overload), 3 (critical)
        """
        logger.info("Criando labels de target com thresholds configuráveis...")
        
        # Labels de sobrecarga de memória
        if 'memory_usage_percent' in df.columns:
            df['memory_warning'] = (df['memory_usage_percent'] > self.thresholds.memory_warning).astype(int)
            df['memory_overload'] = (df['memory_usage_percent'] > self.thresholds.memory_overload).astype(int)
            df['memory_critical'] = (df['memory_usage_percent'] > self.thresholds.memory_critical).astype(int)
        else:
            df['memory_warning'] = 0
            df['memory_overload'] = 0
            df['memory_critical'] = 0
        
        # Labels de sobrecarga de CPU
        if 'cpu_usage_percent' in df.columns:
            df['cpu_warning'] = (df['cpu_usage_percent'] > self.thresholds.cpu_warning).astype(int)
            df['cpu_overload'] = (df['cpu_usage_percent'] > self.thresholds.cpu_overload).astype(int)
            df['cpu_critical'] = (df['cpu_usage_percent'] > self.thresholds.cpu_critical).astype(int)
        else:
            df['cpu_warning'] = 0
            df['cpu_overload'] = 0
            df['cpu_critical'] = 0
        
        # Labels de sobrecarga de disco
        if 'disk_usage_percent' in df.columns:
            df['disk_warning'] = (df['disk_usage_percent'] > self.thresholds.disk_warning).astype(int)
            df['disk_overload'] = (df['disk_usage_percent'] > self.thresholds.disk_overload).astype(int)
            df['disk_critical'] = (df['disk_usage_percent'] > self.thresholds.disk_critical).astype(int)
        else:
            df['disk_warning'] = 0
            df['disk_overload'] = 0
            df['disk_critical'] = 0
        
        # Label combinada de sobrecarga crítica
        df['critical_overload'] = ((df['memory_critical'] == 1) | 
                                   (df['cpu_critical'] == 1) |
                                   (df['disk_critical'] == 1)).astype(int)
        
        # Severidade de sobrecarga (multi-class: 0=normal, 1=warning, 2=overload, 3=critical)
        df['overload_severity'] = 0  # Normal
        
        # Warning
        warning_condition = ((df['memory_warning'] == 1) | 
                            (df['cpu_warning'] == 1) | 
                            (df['disk_warning'] == 1))
        df.loc[warning_condition, 'overload_severity'] = 1
        
        # Overload
        overload_condition = ((df['memory_overload'] == 1) | 
                             (df['cpu_overload'] == 1) | 
                             (df['disk_overload'] == 1))
        df.loc[overload_condition, 'overload_severity'] = 2
        
        # Critical (sobrescreve overload)
        critical_condition = ((df['memory_critical'] == 1) | 
                             (df['cpu_critical'] == 1) | 
                             (df['disk_critical'] == 1))
        df.loc[critical_condition, 'overload_severity'] = 3
        
        # Estatísticas dos labels
        logger.info("\n📊 Distribuição dos Labels (usando thresholds configuráveis):")
        logger.info(f"   Memory Overload (>{self.thresholds.memory_overload}%): {df['memory_overload'].sum()} / {len(df)} ({df['memory_overload'].mean()*100:.2f}%)")
        logger.info(f"   CPU Overload (>{self.thresholds.cpu_overload}%): {df['cpu_overload'].sum()} / {len(df)} ({df['cpu_overload'].mean()*100:.2f}%)")
        logger.info(f"   Disk Overload (>{self.thresholds.disk_overload}%): {df['disk_overload'].sum()} / {len(df)} ({df['disk_overload'].mean()*100:.2f}%)")
        logger.info(f"   Critical Overload: {df['critical_overload'].sum()} / {len(df)} ({df['critical_overload'].mean()*100:.2f}%)")
        logger.info(f"\n   Severity Distribution:")
        logger.info(f"{df['overload_severity'].value_counts().sort_index()}")
        
        return df


class MLDatasetGenerator:
    """Classe principal para gerar dataset completo para ML"""
    
    def __init__(self, prometheus_url: str, thresholds: Optional[ThresholdConfig] = None,
                 username: Optional[str] = None, password: Optional[str] = None,
                 verify_ssl: bool = True):
        """
        Inicializa gerador de dataset
        
        Args:
            prometheus_url: URL do Prometheus
            thresholds: Configuração de thresholds (usa padrão se None)
            username: Usuário para Basic Auth (opcional)
            password: Senha para Basic Auth (opcional)
            verify_ssl: Verificar certificado SSL (default: True)
        """
        self.connector = PrometheusConnector(prometheus_url, username=username, 
                                             password=password, verify_ssl=verify_ssl)
        self.extractor = MetricsExtractor(self.connector)
        
        # Usa thresholds padrão se não fornecido
        if thresholds is None:
            thresholds = ThresholdConfig()
        
        self.thresholds = thresholds
        self.engineer = FeatureEngineer(thresholds)
        self.dataset = None
    
    def generate_dataset(self, duration_minutes: int = 60, step: str = '30s',
                        pod_filter: Optional[str] = None, 
                        namespace: Optional[str] = None) -> pd.DataFrame:
        """
        Gera dataset completo para ML
        
        Args:
            duration_minutes: Duração da coleta em minutos
            step: Intervalo entre medições
            pod_filter: Filtro regex para pods
            namespace: Namespace específico
        
        Returns:
            DataFrame pronto para ML
        """
        logger.info("="*70)
        logger.info("INICIANDO GERAÇÃO DE DATASET PARA MACHINE LEARNING")
        logger.info("="*70)
        
        # Testa conexão
        if not self.connector.test_connection():
            raise ConnectionError("Não foi possível conectar ao Prometheus")
        
        # Calcula período
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=duration_minutes)
        
        logger.info(f"\nPeríodo: {start_time} até {end_time}")
        logger.info(f"Step: {step}")
        if pod_filter:
            logger.info(f"Filtro de pods: {pod_filter}")
        if namespace:
            logger.info(f"Namespace: {namespace}")
        
        # Extrai métricas
        df_raw = self.extractor.extract_metrics(
            start_time, end_time, step, pod_filter, namespace
        )
        
        if df_raw.empty:
            logger.error("Nenhuma métrica foi coletada!")
            return pd.DataFrame()
        
        # Cria features
        df_ml = self.engineer.create_ml_features(df_raw)
        
        # Remove linhas com muitos valores faltantes
        threshold = len(df_ml.columns) * 0.5
        df_ml = df_ml.dropna(thresh=threshold)
        
        # Preenche valores faltantes restantes
        numeric_columns = df_ml.select_dtypes(include=[np.number]).columns
        df_ml[numeric_columns] = df_ml[numeric_columns].fillna(0)
        
        self.dataset = df_ml
        
        logger.info("\n" + "="*70)
        logger.info("✅ DATASET GERADO COM SUCESSO!")
        logger.info("="*70)
        
        return df_ml
    
    def save_dataset(self, output_path: str = 'kubernetes_ml_dataset', 
                    formats: List[str] = ['csv', 'parquet']):
        """
        Salva dataset em múltiplos formatos
        
        Args:
            output_path: Caminho base para salvar arquivos
            formats: Lista de formatos ('csv', 'parquet', 'json')
        """
        if self.dataset is None or self.dataset.empty:
            logger.error("Dataset vazio, nada para salvar")
            return
        
        logger.info("\n💾 Salvando dataset...")
        
        for fmt in formats:
            file_path = f"{output_path}.{fmt}"
            
            if fmt == 'csv':
                self.dataset.to_csv(file_path, index=False)
            elif fmt == 'parquet':
                self.dataset.to_parquet(file_path, index=False)
            elif fmt == 'json':
                self.dataset.to_json(file_path, orient='records', date_format='iso')
            
            import os
            size_mb = os.path.getsize(file_path) / 1024 / 1024
            logger.info(f"   ✅ {file_path} ({size_mb:.2f} MB)")
        
        # Salva também a configuração de thresholds
        self.thresholds.save_to_file(f"{output_path}_thresholds.json")
    
    def get_dataset_info(self) -> Dict:
        """Retorna informações do dataset gerado"""
        if self.dataset is None or self.dataset.empty:
            return {}
        
        info = {
            'total_records': len(self.dataset),
            'total_features': len(self.dataset.columns),
            'pods_monitored': self.dataset['pod'].nunique() if 'pod' in self.dataset.columns else 0,
            'time_range': {
                'start': str(self.dataset['timestamp'].min()),
                'end': str(self.dataset['timestamp'].max()),
            },
            'thresholds_used': self.thresholds.to_dict(),
            'target_distribution': {
                'memory_overload': int(self.dataset['memory_overload'].sum()),
                'cpu_overload': int(self.dataset['cpu_overload'].sum()),
                'disk_overload': int(self.dataset['disk_overload'].sum()),
                'critical_overload': int(self.dataset['critical_overload'].sum()),
            },
            'features': list(self.dataset.columns)
        }
        
        return info
    
    def print_summary(self):
        """Imprime resumo do dataset"""
        if self.dataset is None or self.dataset.empty:
            print("Dataset vazio")
            return
        
        print("\n" + "="*70)
        print("RESUMO DO DATASET")
        print("="*70)
        
        info = self.get_dataset_info()
        
        print(f"\n📊 Informações Gerais:")
        print(f"   • Total de registros: {info['total_records']:,}")
        print(f"   • Total de features: {info['total_features']}")
        print(f"   • Pods monitorados: {info['pods_monitored']}")
        print(f"   • Período: {info['time_range']['start']} até {info['time_range']['end']}")
        
        print(f"\n⚙️  Thresholds Utilizados:")
        for resource, thresholds in info['thresholds_used'].items():
            print(f"   {resource.capitalize()}:")
            print(f"      Warning: {thresholds['warning']}%")
            print(f"      Overload: {thresholds['overload']}%")
            print(f"      Critical: {thresholds['critical']}%")
        
        print(f"\n🎯 Distribuição dos Targets:")
        print(f"   • Memory Overload: {info['target_distribution']['memory_overload']}")
        print(f"   • CPU Overload: {info['target_distribution']['cpu_overload']}")
        print(f"   • Disk Overload: {info['target_distribution']['disk_overload']}")
        print(f"   • Critical Overload: {info['target_distribution']['critical_overload']}")
        
        print(f"\n📋 Features Disponíveis ({len(info['features'])}):")
        for i, feature in enumerate(info['features'][:20], 1):
            print(f"   {i}. {feature}")
        if len(info['features']) > 20:
            print(f"   ... e mais {len(info['features']) - 20} features")
        
        print("\n📈 Estatísticas das Features Principais:")
        key_features = ['memory_usage_percent', 'cpu_usage_percent', 
                       'disk_usage_percent', 'network_total_bytes']
        for feature in key_features:
            if feature in self.dataset.columns:
                print(f"\n   {feature}:")
                print(f"      Média: {self.dataset[feature].mean():.2f}")
                print(f"      Mediana: {self.dataset[feature].median():.2f}")
                print(f"      Std: {self.dataset[feature].std():.2f}")
                print(f"      Min: {self.dataset[feature].min():.2f}")
                print(f"      Max: {self.dataset[feature].max():.2f}")


def parse_arguments():
    """Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description='Gerador de Dataset ML para Detecção de Sobrecarga em Kubernetes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Uso básico (thresholds padrão)
  python sistema_coleta_dados.py --prometheus-url http://localhost:9090

  # Com autenticação Basic Auth
  python sistema_coleta_dados.py \
    --prometheus-url http://localhost:9090 \
    --username admin \
    --password secret

  # Com autenticação e SSL desabilitado
  python sistema_coleta_dados.py \
    --prometheus-url https://prometheus.example.com \
    --username monitor \
    --password mypass123 \
    --no-verify-ssl

  # Senha via variável de ambiente (mais seguro)
  export PROMETHEUS_PASSWORD="secret"
  python sistema_coleta_dados.py \
    --prometheus-url http://localhost:9090 \
    --username admin \
    --password-env PROMETHEUS_PASSWORD

  # Com thresholds personalizados
  python sistema_coleta_dados.py \
    --prometheus-url http://localhost:9090 \
    --memory-overload 85 \
    --cpu-overload 85 \
    --memory-critical 95

  # Coleta longa com filtros
  python sistema_coleta_dados.py \
    --prometheus-url http://localhost:9090 \
    --duration 120 \
    --step 15s \
    --pod-filter "stress-.*" \
    --namespace stress-test

  # Carregar thresholds de arquivo
  python sistema_coleta_dados.py \
    --prometheus-url http://localhost:9090 \
    --thresholds-file custom_thresholds.json

  # Salvar thresholds atuais
  python sistema_coleta_dados.py \
    --save-thresholds-only \
    --memory-overload 75 \
    --cpu-overload 75 \
    --output thresholds.json
        """
    )
    
    # Argumentos principais
    parser.add_argument('--prometheus-url', type=str, default='http://localhost:9090',
                       help='URL do Prometheus (default: http://localhost:9090)')
    
    # Autenticação
    auth_group = parser.add_argument_group('Autenticação Prometheus')
    auth_group.add_argument('--username', type=str, default=None,
                           help='Usuário para Basic Authentication')
    auth_group.add_argument('--password', type=str, default=None,
                           help='Senha para Basic Authentication (use --password-env para mais segurança)')
    auth_group.add_argument('--password-env', type=str, default=None,
                           help='Nome da variável de ambiente contendo a senha')
    auth_group.add_argument('--no-verify-ssl', action='store_true',
                           help='Desabilitar verificação de certificado SSL (não recomendado em produção)')
    
    parser.add_argument('--duration', type=int, default=60,
                       help='Duração da coleta em minutos (default: 60)')
    
    parser.add_argument('--step', type=str, default='30s',
                       help='Intervalo entre medições (default: 30s)')
    
    parser.add_argument('--pod-filter', type=str, default=None,
                       help='Filtro regex para pods (ex: "stress-.*")')
    
    parser.add_argument('--namespace', type=str, default=None,
                       help='Namespace específico')
    
    parser.add_argument('--output', type=str, default='kubernetes_ml_dataset',
                       help='Nome base do arquivo de saída (default: kubernetes_ml_dataset)')
    
    parser.add_argument('--formats', nargs='+', default=['csv', 'parquet'],
                       choices=['csv', 'parquet', 'json'],
                       help='Formatos de saída (default: csv parquet)')
    
    # Thresholds de Memória
    memory_group = parser.add_argument_group('Thresholds de Memória')
    memory_group.add_argument('--memory-warning', type=float, default=70.0,
                             help='Threshold de warning para memória em %% (default: 70)')
    memory_group.add_argument('--memory-overload', type=float, default=80.0,
                             help='Threshold de sobrecarga para memória em %% (default: 80)')
    memory_group.add_argument('--memory-critical', type=float, default=90.0,
                             help='Threshold crítico para memória em %% (default: 90)')
    
    # Thresholds de CPU
    cpu_group = parser.add_argument_group('Thresholds de CPU')
    cpu_group.add_argument('--cpu-warning', type=float, default=70.0,
                          help='Threshold de warning para CPU em %% (default: 70)')
    cpu_group.add_argument('--cpu-overload', type=float, default=80.0,
                          help='Threshold de sobrecarga para CPU em %% (default: 80)')
    cpu_group.add_argument('--cpu-critical', type=float, default=90.0,
                          help='Threshold crítico para CPU em %% (default: 90)')
    
    # Thresholds de Disco
    disk_group = parser.add_argument_group('Thresholds de Disco')
    disk_group.add_argument('--disk-warning', type=float, default=75.0,
                           help='Threshold de warning para disco em %% (default: 75)')
    disk_group.add_argument('--disk-overload', type=float, default=85.0,
                           help='Threshold de sobrecarga para disco em %% (default: 85)')
    disk_group.add_argument('--disk-critical', type=float, default=95.0,
                           help='Threshold crítico para disco em %% (default: 95)')
    
    # Carregar/Salvar thresholds
    config_group = parser.add_argument_group('Configuração de Thresholds')
    config_group.add_argument('--thresholds-file', type=str, default=None,
                             help='Carregar thresholds de arquivo JSON')
    config_group.add_argument('--save-thresholds', type=str, default=None,
                             help='Salvar thresholds em arquivo JSON')
    config_group.add_argument('--save-thresholds-only', action='store_true',
                             help='Apenas salvar thresholds e sair (não coletar dados)')
    
    return parser.parse_args()


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    args = parse_arguments()
    
    try:
        # Obter senha de variável de ambiente se especificado
        password = args.password
        if args.password_env:
            import os
            password = os.getenv(args.password_env)
            if not password:
                logger.error(f"❌ Variável de ambiente '{args.password_env}' não encontrada")
                exit(1)
            logger.info(f"✅ Senha carregada da variável de ambiente: {args.password_env}")
        
        # Validar autenticação
        if args.username and not password:
            logger.error("❌ Username fornecido sem password. Use --password ou --password-env")
            exit(1)
        
        if password and not args.username:
            logger.error("❌ Password fornecido sem username")
            exit(1)
        
        # Carrega ou cria configuração de thresholds
        if args.thresholds_file:
            logger.info(f"📂 Carregando thresholds de: {args.thresholds_file}")
            thresholds = ThresholdConfig.load_from_file(args.thresholds_file)
        else:
            thresholds = ThresholdConfig(
                memory_warning=args.memory_warning,
                memory_overload=args.memory_overload,
                memory_critical=args.memory_critical,
                cpu_warning=args.cpu_warning,
                cpu_overload=args.cpu_overload,
                cpu_critical=args.cpu_critical,
                disk_warning=args.disk_warning,
                disk_overload=args.disk_overload,
                disk_critical=args.disk_critical
            )
        

        # Se for apenas para salvar thresholds
        if args.save_thresholds_only:
            output_file = args.save_thresholds or args.output or 'thresholds_config.json'
            thresholds.save_to_file(output_file)
            logger.info("✅ Thresholds salvos com sucesso!")
            exit(0)

        args.pod_filter = "app-degradacao-.*"
        args.prometheus_url = "http://192.168.242.134:30090/"

        # Cria gerador de dataset com autenticação
        generator = MLDatasetGenerator(
            prometheus_url=args.prometheus_url, 
            thresholds=thresholds,
            username=args.username,
            password=password,
            verify_ssl=not args.no_verify_ssl
        )
        

        # Gera dataset
        df = generator.generate_dataset(
            duration_minutes=args.duration,
            step=args.step,
            pod_filter=args.pod_filter,
            namespace=args.namespace
        )
        
        if df.empty:
            logger.error("❌ Dataset vazio! Verifique se há pods rodando e métricas disponíveis.")
            exit(1)
        
        # Imprime resumo
        generator.print_summary()
        
        # Salva dataset
        generator.save_dataset(
            output_path=args.output,
            formats=args.formats
        )
        
        # Salva thresholds se solicitado
        if args.save_thresholds:
            thresholds.save_to_file(args.save_thresholds)
        
        logger.info("\n✨ Coleta de dados concluída com sucesso!")
        logger.info("\nPróximos passos:")
        logger.info("  1. Treinar modelo: python sistema_treinamento_ml.py")
        logger.info(f"  2. Verificar thresholds: cat {args.output}_thresholds.json")
        logger.info("  3. Ajustar thresholds se necessário e re-executar")
        
    except Exception as e:
        logger.error(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
        exit(1)