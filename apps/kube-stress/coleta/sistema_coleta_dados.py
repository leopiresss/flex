"""
Sistema de Coleta de Métricas para ML - Detecção de Sobrecarga em Kubernetes
Autor: Sistema de Monitoramento
Descrição: Coleta métricas do cAdvisor e gera dataset estruturado para Machine Learning
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PrometheusConnector:
    """Classe para conexão e queries no Prometheus"""
    
    def __init__(self, prometheus_url: str, timeout: int = 60):
        self.prometheus_url = prometheus_url.rstrip('/')
        self.api_url = f"{self.prometheus_url}/api/v1"
        self.timeout = timeout
        logger.info(f"Prometheus Connector iniciado: {self.prometheus_url}")
    
    def test_connection(self) -> bool:
        """Testa conexão com Prometheus"""
        try:
            response = requests.get(f"{self.api_url}/query", 
                                   params={'query': 'up'}, 
                                   timeout=10)
            response.raise_for_status()
            logger.info("✅ Conexão com Prometheus estabelecida")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com Prometheus: {e}")
            return False
    
    def query_range(self, query: str, start: int, end: int, step: str = '30s') -> Optional[Dict]:
        """Executa query com range temporal"""
        try:
            response = requests.get(
                f"{self.api_url}/query_range",
                params={'query': query, 'start': start, 'end': end, 'step': step},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            return None
    
    def query_instant(self, query: str) -> Optional[Dict]:
        """Executa query instantânea"""
        try:
            response = requests.get(
                f"{self.api_url}/query",
                params={'query': query},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
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
            'memory_limit': 'container_spec_memory_limit_bytes',
            'cpu_quota': 'container_spec_cpu_quota',
            'cpu_period': 'container_spec_cpu_period',
            
            # Métricas de Rede
            'network_rx_bytes': 'rate(container_network_receive_bytes_total[5m])',
            'network_tx_bytes': 'rate(container_network_transmit_bytes_total[5m])',
            'network_rx_errors': 'rate(container_network_receive_errors_total[5m])',
            'network_tx_errors': 'rate(container_network_transmit_errors_total[5m])',
            
            # Métricas de Disco
            'fs_usage_bytes': 'container_fs_usage_bytes',
            'fs_limit_bytes': 'container_fs_limit_bytes',
            'fs_reads': 'rate(container_fs_reads_bytes_total[5m])',
            'fs_writes': 'rate(container_fs_writes_bytes_total[5m])',
            
            # Processos
            'processes': 'container_processes',
            'threads': 'container_threads',
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
        
        for metric_name, metric_query in metrics_config.items():
            # Adiciona filtros
            filters = ['container!="POD"', 'container!=""']
            if pod_filter:
                filters.append(f'pod=~"{pod_filter}"')
            if namespace:
                filters.append(f'namespace="{namespace}"')
            
            query = f'{metric_query}{{{",".join(filters)}}}'
            
            logger.info(f"Coletando: {metric_name}")
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
        
        df = pd.DataFrame(all_data)
        logger.info(f"✅ Extração concluída: {len(df)} registros coletados")
        return df


class FeatureEngineer:
    """Classe para engenharia de features para ML"""
    
    def __init__(self):
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
        
        # Cria labels para ML (target)
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
            df['cpu_usage_percent'] = df['cpu_usage_percent'].clip(0, 200)  # Pode ultrapassar em burst
        
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
        Cria labels (targets) para treinamento de ML
        
        Labels criadas:
        - memory_overload: 1 se memória > 80%, 0 caso contrário
        - cpu_overload: 1 se CPU > 80%, 0 caso contrário
        - critical_overload: 1 se memória > 90% OU CPU > 90%
        - overload_severity: 0 (normal), 1 (warning), 2 (critical)
        """
        logger.info("Criando labels de target...")
        
        # Label de sobrecarga de memória
        if 'memory_usage_percent' in df.columns:
            df['memory_overload'] = (df['memory_usage_percent'] > 80).astype(int)
            df['memory_critical'] = (df['memory_usage_percent'] > 90).astype(int)
        else:
            df['memory_overload'] = 0
            df['memory_critical'] = 0
        
        # Label de sobrecarga de CPU
        if 'cpu_usage_percent' in df.columns:
            df['cpu_overload'] = (df['cpu_usage_percent'] > 80).astype(int)
            df['cpu_critical'] = (df['cpu_usage_percent'] > 90).astype(int)
        else:
            df['cpu_overload'] = 0
            df['cpu_critical'] = 0
        
        # Label combinada de sobrecarga crítica
        df['critical_overload'] = ((df['memory_critical'] == 1) | 
                                   (df['cpu_critical'] == 1)).astype(int)
        
        # Severidade de sobrecarga (multi-class)
        df['overload_severity'] = 0  # Normal
        
        if 'memory_usage_percent' in df.columns or 'cpu_usage_percent' in df.columns:
            # Warning: CPU > 70% OU Memória > 70%
            warning_condition = False
            if 'memory_usage_percent' in df.columns:
                warning_condition |= (df['memory_usage_percent'] > 70)
            if 'cpu_usage_percent' in df.columns:
                warning_condition |= (df['cpu_usage_percent'] > 70)
            df.loc[warning_condition, 'overload_severity'] = 1
            
            # Critical: CPU > 90% OU Memória > 90%
            critical_condition = False
            if 'memory_usage_percent' in df.columns:
                critical_condition |= (df['memory_usage_percent'] > 90)
            if 'cpu_usage_percent' in df.columns:
                critical_condition |= (df['cpu_usage_percent'] > 90)
            df.loc[critical_condition, 'overload_severity'] = 2
        
        # Estatísticas dos labels
        logger.info("\n📊 Distribuição dos Labels:")
        logger.info(f"   Memory Overload: {df['memory_overload'].sum()} / {len(df)} ({df['memory_overload'].mean()*100:.2f}%)")
        logger.info(f"   CPU Overload: {df['cpu_overload'].sum()} / {len(df)} ({df['cpu_overload'].mean()*100:.2f}%)")
        logger.info(f"   Critical Overload: {df['critical_overload'].sum()} / {len(df)} ({df['critical_overload'].mean()*100:.2f}%)")
        logger.info(f"\n   Severity Distribution:")
        logger.info(f"{df['overload_severity'].value_counts().sort_index()}")
        
        return df


class MLDatasetGenerator:
    """Classe principal para gerar dataset completo para ML"""
    
    def __init__(self, prometheus_url: str):
        self.connector = PrometheusConnector(prometheus_url)
        self.extractor = MetricsExtractor(self.connector)
        self.engineer = FeatureEngineer()
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
            'target_distribution': {
                'memory_overload': int(self.dataset['memory_overload'].sum()),
                'cpu_overload': int(self.dataset['cpu_overload'].sum()),
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
        
        print(f"\n🎯 Distribuição dos Targets:")
        print(f"   • Memory Overload: {info['target_distribution']['memory_overload']}")
        print(f"   • CPU Overload: {info['target_distribution']['cpu_overload']}")
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


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configurações
    PROMETHEUS_URL = 'http://localhost:9090'
    DURATION_MINUTES = 60  # Coleta últimos 60 minutos
    STEP = '30s'  # Medição a cada 30 segundos
    POD_FILTER = 'memory-stress-.*'  # Filtro opcional
    NAMESPACE = None  # Namespace opcional
    
    # Cria gerador de dataset
    generator = MLDatasetGenerator(PROMETHEUS_URL)
    
    # Gera dataset
    df = generator.generate_dataset(
        duration_minutes=DURATION_MINUTES,
        step=STEP,
        pod_filter=POD_FILTER,
        namespace=NAMESPACE
    )
    
    # Imprime resumo
    generator.print_summary()
    
    # Salva dataset
    generator.save_dataset(
        output_path='kubernetes_ml_dataset',
        formats=['csv', 'parquet', 'json']
    )
    
    # Exemplo: visualizar primeiras linhas
    print("\n📋 Primeiras linhas do dataset:")
    print(df.head(10))
    
    # Exemplo: informações sobre colunas
    print("\n📊 Informações das colunas:")
    print(df.info())
    
    print("\n✨ Dataset pronto para Machine Learning!")
    print("\nPróximos passos:")
    print("1. Carregar o dataset: df = pd.read_parquet('kubernetes_ml_dataset.parquet')")
    print("2. Separar features e target: X = df.drop(['target_columns'], axis=1)")
    print("3. Aplicar algoritmos de ML: RandomForest, XGBoost, etc.")