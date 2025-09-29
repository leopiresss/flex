#!/usr/bin/env python3
"""
Gerador de Dataset para Machine Learning - Degradação de Pods Kubernetes
Coleta métricas do Prometheus e gera dataset estruturado para análise de ML
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import argparse
import sys
from typing import Dict, List, Optional, Tuple, Union
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

warnings.filterwarnings('ignore')

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PrometheusMLDatasetGenerator:
    """Gerador de dataset ML com métricas de degradação de pod"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090",
                 container_name: str = "prime-server",
                 namespace: str = None,
                 timeout: int = 30):
        self.prometheus_url = prometheus_url.rstrip('/')
        self.container_name = container_name
        self.namespace = namespace
        self.timeout = timeout
        
        # Validação da conexão
        if not self._validate_connection():
            raise ConnectionError("Não foi possível conectar ao Prometheus")
        
        # Definição das queries das métricas principais
        self.metric_queries = self._define_metric_queries()
        
        logger.info(f"Gerador inicializado para container '{container_name}' no Prometheus '{prometheus_url}'")
        
    def _validate_connection(self) -> bool:
        """Valida conexão com Prometheus"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/status/config", timeout=10)
            return response.status_code == 200
        except:
            return False
        
    def _build_selector(self) -> str:
        """Constrói seletor base para queries"""
        selector = f'{{container="{self.container_name}"'
        if self.namespace:
            selector += f', namespace="{self.namespace}"'
        selector += '}'
        return selector
        
    def _define_metric_queries(self) -> Dict[str, str]:
        """Define as queries para cada métrica"""
        selector = self._build_selector()
        
        queries = {
            # === MÉTRICAS DE MEMÓRIA ===
            'memory_working_set_bytes': f'container_memory_working_set_bytes{selector}',
            'memory_rss_bytes': f'container_memory_rss{selector}',
            'memory_usage_bytes': f'container_memory_usage_bytes{selector}',
            'memory_cache_bytes': f'container_memory_cache{selector}',
            'memory_limit_bytes': f'container_spec_memory_limit_bytes{selector}',
            'memory_swap_bytes': f'container_memory_swap{selector}',
            
            # === MÉTRICAS DE CPU ===
            'cpu_usage_rate': f'rate(container_cpu_usage_seconds_total{selector}[2m])',
            'cpu_throttled_rate': f'rate(container_cpu_cfs_throttled_seconds_total{selector}[2m])',
            'cpu_periods_rate': f'rate(container_cpu_cfs_periods_total{selector}[2m])',
            'cpu_quota': f'container_spec_cpu_quota{selector}',
            'cpu_shares': f'container_spec_cpu_shares{selector}',
            
            # === MÉTRICAS DE REDE ===
            'network_rx_bytes_rate': f'rate(container_network_receive_bytes_total{selector}[2m])',
            'network_tx_bytes_rate': f'rate(container_network_transmit_bytes_total{selector}[2m])',
            'network_rx_packets_rate': f'rate(container_network_receive_packets_total{selector}[2m])',
            'network_tx_packets_rate': f'rate(container_network_transmit_packets_total{selector}[2m])',
            'network_rx_dropped_rate': f'rate(container_network_receive_packets_dropped_total{selector}[2m])',
            'network_tx_dropped_rate': f'rate(container_network_transmit_packets_dropped_total{selector}[2m])',
            'network_rx_errors_rate': f'rate(container_network_receive_errors_total{selector}[2m])',
            'network_tx_errors_rate': f'rate(container_network_transmit_errors_total{selector}[2m])',
            
            # === MÉTRICAS DE I/O ===
            'fs_reads_bytes_rate': f'rate(container_fs_reads_bytes_total{selector}[2m])',
            'fs_writes_bytes_rate': f'rate(container_fs_writes_bytes_total{selector}[2m])',
            'fs_reads_total_rate': f'rate(container_fs_reads_total{selector}[2m])',
            'fs_writes_total_rate': f'rate(container_fs_writes_total{selector}[2m])',
            'fs_io_time_rate': f'rate(container_fs_io_time_seconds_total{selector}[2m])',
            'fs_usage_bytes': f'container_fs_usage_bytes{selector}',
            'fs_limit_bytes': f'container_fs_limit_bytes{selector}',
            
            # === MÉTRICAS DE POD ===
            'pod_restarts': f'kube_pod_container_status_restarts_total{{container="{self.container_name}"' + 
                           (f', namespace="{self.namespace}"' if self.namespace else '') + '}',
            'pod_ready': f'kube_pod_status_ready{{pod=~".*{self.container_name}.*"}}',
            'pod_phase_running': f'kube_pod_status_phase{{pod=~".*{self.container_name}.*", phase="Running"}}',
        }
        
        # Remove queries com valores None ou vazios
        return {k: v for k, v in queries.items() if v}
    
    def _query_single_metric(self, metric_name: str, query: str, 
                           start_time: int, end_time: int, step: str) -> Dict[str, List]:
        """Executa query única e retorna dados formatados"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params={
                    "query": query,
                    "start": start_time,
                    "end": end_time,
                    "step": step
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} para métrica '{metric_name}'")
                return {"timestamps": [], "values": []}
            
            data = response.json()
            
            if data.get('status') != 'success':
                logger.warning(f"Query falhou para '{metric_name}': {data.get('error', 'Unknown error')}")
                return {"timestamps": [], "values": []}
            
            results = data.get('data', {}).get('result', [])
            if not results:
                logger.debug(f"Nenhum dado encontrado para '{metric_name}'")
                return {"timestamps": [], "values": []}
            
            # Processa primeiro resultado (assumindo um pod/container)
            values_data = results[0].get('values', [])
            if not values_data:
                return {"timestamps": [], "values": []}
            
            timestamps = [float(item[0]) for item in values_data]
            values = []
            
            for item in values_data:
                try:
                    # Converte valor para float, tratando casos especiais
                    val = item[1]
                    if val in ['NaN', '+Inf', '-Inf']:
                        values.append(np.nan)
                    else:
                        values.append(float(val))
                except (ValueError, TypeError):
                    values.append(np.nan)
            
            return {"timestamps": timestamps, "values": values}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede para métrica '{metric_name}': {e}")
            return {"timestamps": [], "values": []}
        except Exception as e:
            logger.error(f"Erro inesperado para métrica '{metric_name}': {e}")
            return {"timestamps": [], "values": []}
    
    def collect_metrics_data(self, duration_hours: int = 24, 
                           step_seconds: int = 30, 
                           max_workers: int = 5) -> pd.DataFrame:
        """Coleta todas as métricas usando threads paralelas"""
        
        logger.info(f"Iniciando coleta de métricas:")
        logger.info(f"  Duração: {duration_hours} horas")
        logger.info(f"  Resolução: {step_seconds} segundos")
        logger.info(f"  Container: {self.container_name}")
        logger.info(f"  Métricas: {len(self.metric_queries)}")
        
        # Calcula período
        end_time = int(time.time())
        start_time = end_time - (duration_hours * 3600)
        step = f"{step_seconds}s"
        
        # Coleta dados usando threads
        all_metrics_data = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submete todas as queries
            future_to_metric = {
                executor.submit(
                    self._query_single_metric, 
                    metric_name, 
                    query, 
                    start_time, 
                    end_time, 
                    step
                ): metric_name
                for metric_name, query in self.metric_queries.items()
            }
            
            # Coleta resultados
            completed = 0
            total = len(future_to_metric)
            
            for future in as_completed(future_to_metric):
                metric_name = future_to_metric[future]
                completed += 1
                
                try:
                    result = future.result()
                    all_metrics_data[metric_name] = result
                    
                    if result["timestamps"]:
                        logger.info(f"[{completed}/{total}] ✅ {metric_name}: {len(result['timestamps'])} pontos")
                    else:
                        logger.warning(f"[{completed}/{total}] ⚠️  {metric_name}: sem dados")
                        
                except Exception as e:
                    logger.error(f"[{completed}/{total}] ❌ {metric_name}: {e}")
                    all_metrics_data[metric_name] = {"timestamps": [], "values": []}
        
        # Converte para DataFrame
        df = self._build_dataframe(all_metrics_data)
        
        if df.empty:
            logger.error("❌ Nenhum dado coletado!")
            return pd.DataFrame()
        
        logger.info(f"✅ Dataset base criado: {len(df)} registros, {len(df.columns)} colunas")
        return df
    
    def _build_dataframe(self, metrics_data: Dict[str, Dict]) -> pd.DataFrame:
        """Constrói DataFrame a partir dos dados coletados"""
        
        # Encontra conjunto comum de timestamps
        all_timestamps = set()
        valid_metrics = {}
        
        for metric_name, data in metrics_data.items():
            if data["timestamps"]:
                all_timestamps.update(data["timestamps"])
                valid_metrics[metric_name] = data
        
        if not all_timestamps:
            return pd.DataFrame()
        
        # Ordena timestamps
        sorted_timestamps = sorted(list(all_timestamps))
        
        # Constrói DataFrame
        df_data = {"timestamp": sorted_timestamps}
        
        for metric_name, data in valid_metrics.items():
            # Cria série temporal completa, preenchendo valores faltantes com NaN
            metric_series = pd.Series(
                data["values"], 
                index=data["timestamps"]
            ).reindex(sorted_timestamps)
            
            df_data[metric_name] = metric_series.values
        
        df = pd.DataFrame(df_data)
        
        # Adiciona coluna datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        return df
    
    def calculate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula features derivadas para ML"""
        if df.empty:
            return df
        
        logger.info("🧮 Calculando features derivadas...")
        df = df.copy()
        
        # === CONVERSÕES DE UNIDADE ===
        # Converte bytes para MB
        byte_columns = [col for col in df.columns if 'bytes' in col.lower() and 'rate' not in col]
        for col in byte_columns:
            if col in df.columns:
                df[f'{col}_mb'] = df[col] / (1024 * 1024)
        
        # === PERCENTUAIS DE USO ===
        if 'memory_working_set_bytes' in df.columns and 'memory_limit_bytes' in df.columns:
            df['memory_usage_percent'] = np.where(
                df['memory_limit_bytes'] > 0,
                (df['memory_working_set_bytes'] / df['memory_limit_bytes']) * 100,
                0
            )
        
        if 'memory_rss_bytes' in df.columns and 'memory_limit_bytes' in df.columns:
            df['memory_rss_percent'] = np.where(
                df['memory_limit_bytes'] > 0,
                (df['memory_rss_bytes'] / df['memory_limit_bytes']) * 100,
                0
            )
        
        if 'fs_usage_bytes' in df.columns and 'fs_limit_bytes' in df.columns:
            df['disk_usage_percent'] = np.where(
                df['fs_limit_bytes'] > 0,
                (df['fs_usage_bytes'] / df['fs_limit_bytes']) * 100,
                0
            )
        
        # === CPU FEATURES ===
        # CPU como percentual (rate já está normalizado)
        if 'cpu_usage_rate' in df.columns:
            df['cpu_usage_percent'] = df['cpu_usage_rate'] * 100
        
        # CPU throttling percentage
        if 'cpu_throttled_rate' in df.columns and 'cpu_periods_rate' in df.columns:
            df['cpu_throttling_percent'] = np.where(
                df['cpu_periods_rate'] > 0,
                (df['cpu_throttled_rate'] / df['cpu_periods_rate']) * 100,
                0
            )
        
        # === NETWORK FEATURES ===
        if 'network_rx_bytes_rate' in df.columns and 'network_tx_bytes_rate' in df.columns:
            df['network_total_bytes_rate'] = df['network_rx_bytes_rate'] + df['network_tx_bytes_rate']
            df['network_total_mbps'] = (df['network_total_bytes_rate'] * 8) / (1024 * 1024)  # Mbps
        
        # Network drop rate
        if all(col in df.columns for col in ['network_rx_dropped_rate', 'network_tx_dropped_rate', 
                                           'network_rx_packets_rate', 'network_tx_packets_rate']):
            total_drops = df['network_rx_dropped_rate'] + df['network_tx_dropped_rate']
            total_packets = df['network_rx_packets_rate'] + df['network_tx_packets_rate']
            
            df['network_drop_percent'] = np.where(
                total_packets > 0,
                (total_drops / total_packets) * 100,
                0
            )
        
        # Network error rate
        if all(col in df.columns for col in ['network_rx_errors_rate', 'network_tx_errors_rate']):
            df['network_total_errors_rate'] = df['network_rx_errors_rate'] + df['network_tx_errors_rate']
        
        # === I/O FEATURES ===
        if 'fs_reads_bytes_rate' in df.columns and 'fs_writes_bytes_rate' in df.columns:
            df['fs_total_io_bytes_rate'] = df['fs_reads_bytes_rate'] + df['fs_writes_bytes_rate']
            df['fs_total_io_mbps'] = df['fs_total_io_bytes_rate'] / (1024 * 1024)
        
        if 'fs_reads_total_rate' in df.columns and 'fs_writes_total_rate' in df.columns:
            df['fs_total_iops'] = df['fs_reads_total_rate'] + df['fs_writes_total_rate']
        
        # === FEATURES TEMPORAIS ===
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['minute'] = df['datetime'].dt.minute
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Períodos do dia
        df['time_period'] = pd.cut(
            df['hour'], 
            bins=[0, 6, 12, 18, 24], 
            labels=['night', 'morning', 'afternoon', 'evening'],
            include_lowest=True
        ).astype(str)
        
        # === ROLLING STATISTICS ===
        self._calculate_rolling_features(df)
        
        # === LAG FEATURES ===
        self._calculate_lag_features(df)
        
        # === ANOMALY SCORES ===
        self._calculate_anomaly_scores(df)
        
        logger.info(f"✅ Features derivadas calculadas. Total: {len(df.columns)} colunas")
        return df
    
    def _calculate_rolling_features(self, df: pd.DataFrame) -> None:
        """Calcula features de janela móvel"""
        window_sizes = [5, 10, 30, 60]
        key_metrics = ['memory_usage_percent', 'cpu_usage_percent', 'network_total_bytes_rate', 'fs_total_io_bytes_rate']
        
        for metric in key_metrics:
            if metric in df.columns:
                for window in window_sizes:
                    if len(df) >= window:
                        # Média móvel
                        df[f'{metric}_ma_{window}'] = df[metric].rolling(window=window, min_periods=1).mean()
                        
                        # Desvio padrão móvel
                        df[f'{metric}_std_{window}'] = df[metric].rolling(window=window, min_periods=1).std()
                        
                        # Máximo e mínimo móvel
                        df[f'{metric}_max_{window}'] = df[metric].rolling(window=window, min_periods=1).max()
                        df[f'{metric}_min_{window}'] = df[metric].rolling(window=window, min_periods=1).min()
    
    def _calculate_lag_features(self, df: pd.DataFrame) -> None:
        """Calcula features de lag temporal"""
        lag_periods = [1, 5, 10, 30]
        key_metrics = ['memory_usage_percent', 'cpu_usage_percent', 'network_total_bytes_rate']
        
        for metric in key_metrics:
            if metric in df.columns:
                for lag in lag_periods:
                    # Diferença
                    df[f'{metric}_diff_{lag}'] = df[metric].diff(lag)
                    
                    # Taxa de mudança percentual
                    df[f'{metric}_pct_change_{lag}'] = df[metric].pct_change(lag) * 100
                    
                    # Valor anterior (lag)
                    if lag <= 10:  # Limita para não criar muitas colunas
                        df[f'{metric}_lag_{lag}'] = df[metric].shift(lag)
    
    def _calculate_anomaly_scores(self, df: pd.DataFrame) -> None:
        """Calcula scores de anomalia"""
        key_metrics = ['memory_usage_percent', 'cpu_usage_percent', 'network_total_bytes_rate']
        
        for metric in key_metrics:
            if metric in df.columns:
                # Z-score (padronização)
                mean_val = df[metric].mean()
                std_val = df[metric].std()
                if std_val > 0:
                    df[f'{metric}_zscore'] = (df[metric] - mean_val) / std_val
                
                # IQR score
                q75, q25 = df[metric].quantile([0.75, 0.25])
                iqr = q75 - q25
                if iqr > 0:
                    df[f'{metric}_iqr_score'] = (df[metric] - q25) / iqr
                
                # Modified Z-score usando mediana
                median_val = df[metric].median()
                mad = np.median(np.abs(df[metric] - median_val))
                if mad > 0:
                    df[f'{metric}_modified_zscore'] = 0.6745 * (df[metric] - median_val) / mad
    
    def create_degradation_labels(self, df: pd.DataFrame, 
                                custom_thresholds: Dict[str, float] = None) -> pd.DataFrame:
        """Cria labels de degradação para supervised learning"""
        if df.empty:
            return df
        
        logger.info("🏷️  Criando labels de degradação...")
        df = df.copy()
        
        # Thresholds padrão
        thresholds = {
            'memory_percent': 80.0,
            'cpu_percent': 80.0,
            'cpu_throttling_percent': 10.0,
            'disk_percent': 85.0,
            'network_drop_percent': 1.0,
            'restart_threshold': 1  # qualquer restart indica problema
        }
        
        # Atualiza com thresholds customizados
        if custom_thresholds:
            thresholds.update(custom_thresholds)
        
        # Inicializa labels
        df['degradation_level'] = 0  # 0: Normal
        df['is_degraded'] = 0        # Binary
        
        # Lista de condições de degradação
        degradation_conditions = []
        condition_names = []
        
        # === CONDIÇÕES DE DEGRADAÇÃO ===
        
        # 1. Memória alta
        if 'memory_usage_percent' in df.columns:
            memory_degraded = df['memory_usage_percent'] > thresholds['memory_percent']
            degradation_conditions.append(memory_degraded)
            condition_names.append('high_memory')
            df['degradation_memory'] = memory_degraded.astype(int)
        
        # 2. CPU alta
        if 'cpu_usage_percent' in df.columns:
            cpu_degraded = df['cpu_usage_percent'] > thresholds['cpu_percent']
            degradation_conditions.append(cpu_degraded)
            condition_names.append('high_cpu')
            df['degradation_cpu'] = cpu_degraded.astype(int)
        
        # 3. CPU throttling
        if 'cpu_throttling_percent' in df.columns:
            throttling_degraded = df['cpu_throttling_percent'] > thresholds['cpu_throttling_percent']
            degradation_conditions.append(throttling_degraded)
            condition_names.append('cpu_throttling')
            df['degradation_throttling'] = throttling_degraded.astype(int)
        
        # 4. Disk usage alto
        if 'disk_usage_percent' in df.columns:
            disk_degraded = df['disk_usage_percent'] > thresholds['disk_percent']
            degradation_conditions.append(disk_degraded)
            condition_names.append('high_disk')
            df['degradation_disk'] = disk_degraded.astype(int)
        
        # 5. Network drops
        if 'network_drop_percent' in df.columns:
            network_degraded = df['network_drop_percent'] > thresholds['network_drop_percent']
            degradation_conditions.append(network_degraded)
            condition_names.append('network_drops')
            df['degradation_network'] = network_degraded.astype(int)
        
        # 6. Pod restarts
        if 'pod_restarts' in df.columns:
            restart_degraded = df['pod_restarts'].diff() >= thresholds['restart_threshold']
            restart_degraded = restart_degraded.fillna(False)
            degradation_conditions.append(restart_degraded)
            condition_names.append('pod_restarts')
            df['degradation_restarts'] = restart_degraded.astype(int)
        
        # === CRIAÇÃO DOS LABELS ===
        if degradation_conditions:
            # Conta quantas condições são verdadeiras para cada linha
            total_conditions = sum(degradation_conditions)
            
            # Labels multi-classe baseados na severidade
            df.loc[total_conditions == 1, 'degradation_level'] = 1  # Leve
            df.loc[(total_conditions >= 2) & (total_conditions <= 3), 'degradation_level'] = 2  # Moderada
            df.loc[total_conditions >= 4, 'degradation_level'] = 3  # Severa
            
            # Label binário
            df.loc[total_conditions > 0, 'is_degraded'] = 1
            
            # Condições individuais como features
            df['degradation_score'] = total_conditions  # Score numérico
        
        # === ESTATÍSTICAS DOS LABELS ===
        self._print_label_statistics(df, condition_names)
        
        return df
    
    def _print_label_statistics(self, df: pd.DataFrame, condition_names: List[str]) -> None:
        """Imprime estatísticas dos labels"""
        logger.info("📊 Distribuição de labels:")
        
        # Distribuição multi-classe
        if 'degradation_level' in df.columns:
            label_counts = df['degradation_level'].value_counts().sort_index()
            labels = ['Normal', 'Leve', 'Moderada', 'Severa']
            
            for level, count in label_counts.items():
                if level < len(labels):
                    pct = count / len(df) * 100
                    logger.info(f"   {labels[level]}: {count} ({pct:.1f}%)")
        
        # Distribuição das condições individuais
        if condition_names:
            logger.info("📋 Condições de degradação:")
            for condition in condition_names:
                col_name = f'degradation_{condition.replace("high_", "").replace("_", "")}'
                if col_name in df.columns:
                    count = df[col_name].sum()
                    pct = count / len(df) * 100
                    logger.info(f"   {condition}: {count} ({pct:.1f}%)")
    
    def clean_dataset(self, df: pd.DataFrame, 
                     max_missing_percent: float = 30.0,
                     fill_strategy: str = 'median') -> pd.DataFrame:
        """Limpa e prepara dataset para ML"""
        if df.empty:
            return df
        
        logger.info("🧹 Limpando dataset...")
        df = df.copy()
        
        initial_rows = len(df)
        initial_cols = len(df.columns)
        
        # Remove colunas com muitos valores faltantes
        missing_percent = (df.isnull().sum() / len(df)) * 100
        cols_to_drop = missing_percent[missing_percent > max_missing_percent].index.tolist()
        
        if cols_to_drop:
            logger.info(f"   Removendo {len(cols_to_drop)} colunas com >{max_missing_percent}% missing")
            df = df.drop(columns=cols_to_drop)
        
        # Remove linhas com muitos valores faltantes
        row_threshold = len(df.columns) * (1 - max_missing_percent / 100)
        df = df.dropna(thresh=int(row_threshold))
        
        # Preenche valores faltantes remanescentes
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col not in ['timestamp']:
                if fill_strategy == 'median':
                    df[col] = df[col].fillna(df[col].median())
                elif fill_strategy == 'mean':
                    df[col] = df[col].fillna(df[col].mean())
                elif fill_strategy == 'zero':
                    df[col] = df[col].fillna(0)
                elif fill_strategy == 'forward':
                    df[col] = df[col].fillna(method='ffill')
        
        # Preenche colunas categóricas
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if col not in ['datetime']:
                df[col] = df[col].fillna('unknown')
        
        # Remove linhas duplicadas baseadas no timestamp
        if 'timestamp' in df.columns:
            df = df.drop_duplicates(subset=['timestamp'], keep='last')
        
        # Remove colunas constantes (variância zero)
        constant_cols = []
        for col in numeric_cols:
            if df[col].nunique() <= 1:
                constant_cols.append(col)
        
        if constant_cols:
            logger.info(f"   Removendo {len(constant_cols)} colunas constantes")
            df = df.drop(columns=constant_cols)
        
        # Remove outliers extremos (opcional)
        # self._remove_extreme_outliers(df, numeric_cols)
        
        final_rows = len(df)
        final_cols = len(df.columns)
        
        logger.info(f"   Linhas: {initial_rows} → {final_rows} ({((final_rows-initial_rows)/initial_rows)*100:+.1f}%)")
        logger.info(f"   Colunas: {initial_cols} → {final_cols} ({((final_cols-initial_cols)/initial_cols)*100:+.1f}%)")
        
        return df
    
    def export_dataset(self, df: pd.DataFrame, 
                      filename: str = None, 
                      format: str = 'csv',
                      include_metadata: bool = True) -> str:
        """Exporta dataset em diferentes formatos"""
        if df.empty:
            logger.error("❌ Dataset vazio, nada para exportar")
            return None
        
        # Gera nome do arquivo se não fornecido
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pod_degradation_dataset_{self.container_name}_{timestamp}"
        
        # Remove extensão se fornecida
        filename = filename.replace('.csv', '').replace('.parquet', '').replace('.json', '')
        
        # Prepara dados para exportação
        export_df = df.copy()
        
        # Remove colunas de debugging se existirem
        debug_cols = [col for col in export_df.columns if col.startswith('debug_')]
        if debug_cols:
            export_df = export_df.drop(columns=debug_cols)
        
        try:
            if format.lower() == 'csv':
                filepath = f"{filename}.csv"
                export_df.to_csv(filepath, index=False, float_format='%.6f')
                
            elif format.lower() == 'parquet':
                filepath = f"{filename}.parquet"
                export_df.to_parquet(filepath, index=False, engine='pyarrow')
                
            elif format.lower() == 'json':
                filepath = f"{filename}.json"
                export_df.to_json(filepath, orient='records', date_format='iso', indent=2)
                
            else:
                logger.error(f"❌ Formato não suportado: {format}")
                return None
            
            # Cria arquivo de metadados se solicitado
            if include_metadata:
                self._create_metadata_file(df, filepath)
            
            # Estatísticas do arquivo
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            logger.info(f"✅ Dataset exportado: {filepath}")
            logger.info(f"   Registros: {len(export_df):,}")
            logger.info(f"   Colunas: {len(export_df.columns)}")
            logger.info(f"   Tamanho: {file_size_mb:.2f} MB")
            logger.info(f"   Período: {export_df['datetime'].min()} até {export_df['datetime'].max()}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar dataset: {e}")
            return None
    
    def _create_metadata_file(self, df: pd.DataFrame, dataset_filepath: str) -> None:
        """Cria arquivo de metadados do dataset"""
        metadata = {
            "dataset_info": {
                "filename": os.path.basename(dataset_filepath),
                "created_at": datetime.now().isoformat(),
                "container_name": self.container_name,
                "namespace": self.namespace,
                "prometheus_url": self.prometheus_url
            },
            "data_summary": {
                "total_records": len(df),
                "total_columns": len(df.columns),
                "start_time": df['datetime'].min().isoformat(),
                "end_time": df['datetime'].max().isoformat(),
                "duration_hours": (df['datetime'].max() - df['datetime'].min()).total_seconds() / 3600
            },
            "column_info": {},
            "label_distribution": {},
            "data_quality": {}
        }
        
        # Informações das colunas
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].count()),
                "null_count": int(df[col].isnull().sum()),
                "null_percentage": float((df[col].isnull().sum() / len(df)) * 100)
            }
            
            if df[col].dtype in ['float64', 'int64']:
                col_info.update({
                    "mean": float(df[col].mean()) if not df[col].empty else None,
                    "std": float(df[col].std()) if not df[col].empty else None,
                    "min": float(df[col].min()) if not df[col].empty else None,
                    "max": float(df[col].max()) if not df[col].empty else None
                })
            
            metadata["column_info"][col] = col_info
        
        # Distribuição de labels
        if 'degradation_level' in df.columns:
            metadata["label_distribution"]["degradation_level"] = df['degradation_level'].value_counts().to_dict()
        
        if 'is_degraded' in df.columns:
            metadata["label_distribution"]["is_degraded"] = df['is_degraded'].value_counts().to_dict()
        
        # Qualidade dos dados
        metadata["data_quality"] = {
            "total_missing_values": int(df.isnull().sum().sum()),
            "missing_percentage": float((df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100),
            "duplicate_rows": int(df.duplicated().sum())
        }
        
        # Salva metadados
        metadata_path = dataset_filepath.replace('.csv', '').replace('.parquet', '').replace('.json', '') + '_metadata.json'
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"📋 Metadados salvos: {metadata_path}")
    
    def generate_ml_ready_dataset(self, 
                                 duration_hours: int = 24,
                                 step_seconds: int = 30,
                                 include_labels: bool = True,
                                 custom_thresholds: Dict[str, float] = None,
                                 export_format: str = 'csv',
                                 filename: str = None,
                                 max_missing_percent: float = 30.0,
                                 fill_strategy: str = 'median') -> Tuple[pd.DataFrame, str]:
        """Pipeline completo para gerar dataset pronto para ML"""
        
        logger.info("🤖 GERAÇÃO DE DATASET PARA MACHINE LEARNING")
        logger.info("=" * 60)
        
        try:
            # 1. Coleta dados básicos
            df = self.collect_metrics_data(duration_hours, step_seconds)
            
            if df.empty:
                logger.error("❌ Falha na coleta de dados")
                return pd.DataFrame(), None
            
            # 2. Calcula features derivadas
            df = self.calculate_derived_features(df)
            
            # 3. Cria labels (se solicitado)
            if include_labels:
                df = self.create_degradation_labels(df, custom_thresholds)
            
            # 4. Limpa dataset
            df = self.clean_dataset(df, max_missing_percent, fill_strategy)
            
            if df.empty:
                logger.error("❌ Dataset vazio após limpeza")
                return pd.DataFrame(), None
            
            # 5. Exporta dataset
            filepath = self.export_dataset(df, filename, export_format, include_metadata=True)
            
            logger.info("\n✅ DATASET PRONTO PARA MACHINE LEARNING!")
            logger.info(f"📊 Shape final: {df.shape}")
            
            return df, filepath
            
        except Exception as e:
            logger.error(f"❌ Erro no pipeline: {e}")
            return pd.DataFrame(), None
    
    def get_feature_importance_ready_columns(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """Retorna listas de colunas de features e targets para ML"""
        
        # Colunas a excluir das features
        exclude_cols = [
            'timestamp', 'datetime',
            'degradation_level', 'is_degraded', 'degradation_score'
        ]
        
        # Adiciona colunas de degradação individual (targets auxiliares)
        degradation_cols = [col for col in df.columns if col.startswith('degradation_')]
        exclude_cols.extend(degradation_cols)
        
        # Features (todas menos as excluídas)
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Targets disponíveis
        target_cols = []
        if 'degradation_level' in df.columns:
            target_cols.append('degradation_level')
        if 'is_degraded' in df.columns:
            target_cols.append('is_degraded')
        
        return feature_cols, target_cols
    
    def print_dataset_summary(self, df: pd.DataFrame) -> None:
        """Imprime resumo detalhado do dataset"""
        if df.empty:
            logger.info("Dataset vazio")
            return
        
        logger.info("\n📋 RESUMO DO DATASET:")
        logger.info("=" * 50)
        
        logger.info(f"Shape: {df.shape}")
        
        if 'datetime' in df.columns:
            duration = df['datetime'].max() - df['datetime'].min()
            logger.info(f"Período: {df['datetime'].min()} até {df['datetime'].max()}")
            logger.info(f"Duração: {duration}")
            
            # Frequência de coleta
            if len(df) > 1:
                avg_interval = duration / (len(df) - 1)
                logger.info(f"Intervalo médio: {avg_interval}")
        
        # Tipos de colunas
        logger.info(f"\n🔢 TIPOS DE COLUNAS:")
        dtype_counts = df.dtypes.value_counts()
        for dtype, count in dtype_counts.items():
            logger.info(f"   {dtype}: {count} colunas")
        
        # Estatísticas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        logger.info(f"\n📊 COLUNAS NUMÉRICAS: {len(numeric_cols)}")
        
        if len(numeric_cols) > 0:
            stats_df = df[numeric_cols].describe()
            logger.info(f"\n{stats_df}")
        
        # Labels (se existirem)
        if 'degradation_level' in df.columns:
            logger.info(f"\n🏷️  DISTRIBUIÇÃO DE LABELS:")
            label_counts = df['degradation_level'].value_counts().sort_index()
            labels = ['Normal', 'Leve', 'Moderada', 'Severa']
            
            for level, count in label_counts.items():
                if level < len(labels):
                    pct = count / len(df) * 100
                    logger.info(f"   {labels[level]}: {count:,} ({pct:.1f}%)")
        
        # Valores faltantes
        missing = df.isnull().sum()
        missing_pct = (missing / len(df)) * 100
        missing_info = pd.DataFrame({
            'Missing_Count': missing,
            'Missing_Percent': missing_pct
        })
        missing_info = missing_info[missing_info['Missing_Count'] > 0].sort_values('Missing_Count', ascending=False)
        
        if len(missing_info) > 0:
            logger.info(f"\n❌ VALORES FALTANTES (Top 10):")
            logger.info(f"\n{missing_info.head(10)}")
        else:
            logger.info(f"\n✅ NENHUM VALOR FALTANTE!")
        
        # Features vs Targets
        feature_cols, target_cols = self.get_feature_importance_ready_columns(df)
        logger.info(f"\n🎯 PREPARAÇÃO PARA ML:")
        logger.info(f"   Features disponíveis: {len(feature_cols)}")
        logger.info(f"   Targets disponíveis: {len(target_cols)}")
        
        if target_cols:
            logger.info(f"   Targets: {', '.join(target_cols)}")

# Adiciona import necessário
import os

def main():
    parser = argparse.ArgumentParser(
        description='Gerador de Dataset ML para Degradação de Pods Kubernetes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python ml_dataset_generator.py --hours 48 --step 15
  python ml_dataset_generator.py --prometheus http://prometheus:9090 --container my-app --hours 72
  python ml_dataset_generator.py --format parquet --filename meu_dataset --no-labels
  python ml_dataset_generator.py --custom-thresholds memory_percent=85 cpu_percent=75
        """
    )
    
    parser.add_argument('--prometheus', default='http://localhost:9090',
                       help='URL do Prometheus (padrão: http://localhost:9090)')
    parser.add_argument('--container', default='prime-server',
                       help='Nome do container (padrão: prime-server)')
    parser.add_argument('--namespace', default=None,
                       help='Namespace do Kubernetes (opcional)')
    
    parser.add_argument('--hours', type=int, default=24,
                       help='Duração em horas (padrão: 24)')
    parser.add_argument('--step', type=int, default=30,
                       help='Intervalo em segundos (padrão: 30)')
    
    parser.add_argument('--format', choices=['csv', 'parquet', 'json'], default='csv',
                       help='Formato de exportação (padrão: csv)')
    parser.add_argument('--filename', default=None,
                       help='Nome do arquivo (sem extensão)')
    parser.add_argument('--no-labels', action='store_true',
                       help='Não incluir labels de degradação')
    
    parser.add_argument('--max-missing', type=float, default=30.0,
                       help='Máximo percentual de valores faltantes (padrão: 30)')
    parser.add_argument('--fill-strategy', choices=['median', 'mean', 'zero', 'forward'], 
                       default='median', help='Estratégia para preencher NaN (padrão: median)')
    
    parser.add_argument('--custom-thresholds', nargs='*', default=[],
                       help='Thresholds customizados (ex: memory_percent=85 cpu_percent=75)')
    
    parser.add_argument('--workers', type=int, default=5,
                       help='Número de threads para coleta (padrão: 5)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout para queries em segundos (padrão: 30)')
    parser.add_argument('--verbose', action='store_true',
                       help='Logging detalhado')
    
    args = parser.parse_args()
    
    # Configura logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Processa thresholds customizados
    custom_thresholds = {}
    for threshold in args.custom_thresholds:
        try:
            key, value = threshold.split('=')
            custom_thresholds[key] = float(value)
        except ValueError:
            logger.warning(f"Threshold inválido ignorado: {threshold}")
    
    try:
        # Cria gerador
        generator = PrometheusMLDatasetGenerator(
            prometheus_url=args.prometheus,
            container_name=args.container,
            namespace=args.namespace,
            timeout=args.timeout
        )
        
        # Gera dataset
        df, filepath = generator.generate_ml_ready_dataset(
            duration_hours=args.hours,
            step_seconds=args.step,
            include_labels=not args.no_labels,
            custom_thresholds=custom_thresholds if custom_thresholds else None,
            export_format=args.format,
            filename=args.filename,
            max_missing_percent=args.max_missing,
            fill_strategy=args.fill_strategy
        )
        
        if df is not None and not df.empty:
            generator.print_dataset_summary(df)
            
            # Informações para uso em ML
            feature_cols, target_cols = generator.get_feature_importance_ready_columns(df)
            
            logger.info(f"\n🎯 PRÓXIMOS PASSOS:")
            logger.info(f"1. Carregue o dataset: df = pd.read_csv('{filepath}')")
            logger.info(f"2. Separe features e targets:")
            logger.info(f"   X = df{feature_cols[:5]}  # {len(feature_cols)} features total")
            if target_cols:
                logger.info(f"   y = df['{target_cols[0]}']  # ou qualquer target disponível")
            logger.info(f"3. Aplique train_test_split, StandardScaler, etc.")
            logger.info(f"4. Treine modelos: RandomForest, XGBoost, etc.")
            
        else:
            logger.error("❌ Falha ao gerar dataset")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\nProcesso interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()