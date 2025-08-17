import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict
import logging

class MetricsProcessor:
    """Processa e analisa métricas coletadas do cAdvisor"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.df = None
    
    def process_raw_metrics(self, raw_metrics: List[Dict]) -> pd.DataFrame:
        """Converte métricas brutas em DataFrame pandas"""
        processed_data = []
        
        for metric in raw_metrics:
            # Flatten nested dictionaries
            flattened = {
                'timestamp': pd.to_datetime(metric['timestamp']),
                'container_path': metric['container_path'],
                'container_name': metric['container_name'],
                
                # CPU metrics
                'cpu_total_usage': metric['cpu_usage']['total_usage'],
                'cpu_system_usage': metric['cpu_usage']['system_usage'],
                'cpu_user_usage': metric['cpu_usage']['user_usage'],
                
                # Memory metrics (convert to MB)
                'memory_usage_mb': metric['memory_usage']['usage'] / (1024 * 1024),
                'memory_working_set_mb': metric['memory_usage']['working_set'] / (1024 * 1024),
                'memory_rss_mb': metric['memory_usage']['rss'] / (1024 * 1024),
                'memory_cache_mb': metric['memory_usage']['cache'] / (1024 * 1024),
                
                # Network metrics (convert to MB)
                'network_rx_mb': metric['network_stats']['rx_bytes'] / (1024 * 1024),
                'network_tx_mb': metric['network_stats']['tx_bytes'] / (1024 * 1024),
                'network_rx_packets': metric['network_stats']['rx_packets'],
                'network_tx_packets': metric['network_stats']['tx_packets'],
                
                # Filesystem metrics (convert to GB)
                'filesystem_usage_gb': metric['filesystem_stats']['total_usage'] / (1024 * 1024 * 1024),
                'filesystem_capacity_gb': metric['filesystem_stats']['total_capacity'] / (1024 * 1024 * 1024)
            }
            
            processed_data.append(flattened)
        
        self.df = pd.DataFrame(processed_data)
        self.logger.info(f"Processados {len(self.df)} registros de métricas")
        return self.df
    
    def calculate_cpu_percentage(self, machine_info: Dict) -> pd.DataFrame:
        """Calcula percentual de uso de CPU"""
        if self.df is None:
            raise ValueError("Dados não processados. Execute process_raw_metrics primeiro.")
        
        # Número de CPUs da máquina
        num_cpus = machine_info.get('num_cores', 1)
        
        # Calcular diferenças para obter taxa de uso
        df_sorted = self.df.sort_values(['container_name', 'timestamp'])
        df_sorted['cpu_usage_rate'] = df_sorted.groupby('container_name')['cpu_total_usage'].diff()
        df_sorted['cpu_system_rate'] = df_sorted.groupby('container_name')['cpu_system_usage'].diff()
        
        # Calcular percentual (assumindo nanosegundos)
        df_sorted['cpu_usage_percent'] = (df_sorted['cpu_usage_rate'] / 1e9) * 100 / num_cpus
        
        return df_sorted
    
    def get_summary_statistics(self) -> Dict:
        """Gera estatísticas resumidas das métricas"""
        if self.df is None:
            raise ValueError("Dados não processados. Execute process_raw_metrics primeiro.")
        
        numeric_columns = self.df.select_dtypes(include=[np.number]).columns
        
        summary = {
            'total_containers': self.df['container_name'].nunique(),
            'total_records': len(self.df),
            'time_range': {
                'start': self.df['timestamp'].min().isoformat(),
                'end': self.df['timestamp'].max().isoformat(),
                'duration_minutes': (self.df['timestamp'].max() - self.df['timestamp'].min()).total_seconds() / 60
            },
            'metrics_summary': {}
        }
        
        for col in numeric_columns:
            if col != 'timestamp':
                summary['metrics_summary'][col] = {
                    'mean': float(self.df[col].mean()),
                    'median': float(self.df[col].median()),
                    'std': float(self.df[col].std()),
                    'min': float(self.df[col].min()),
                    'max': float(self.df[col].max())
                }
        
        return summary
    
    def get_top_consumers(self, metric: str, top_n: int = 5) -> pd.DataFrame:
        """Identifica os maiores consumidores de um recurso específico"""
        if self.df is None:
            raise ValueError("Dados não processados. Execute process_raw_metrics primeiro.")
        
        if metric not in self.df.columns:
            raise ValueError(f"Métrica '{metric}' não encontrada nos dados")
        
        top_consumers = (self.df.groupby('container_name')[metric]
                        .agg(['mean', 'max', 'std'])
                        .sort_values('mean', ascending=False)
                        .head(top_n))
        
        return top_consumers
    
    def detect_anomalies(self, metric: str, threshold_std: float = 2.0) -> pd.DataFrame:
        """Detecta anomalias usando desvio padrão"""
        if self.df is None:
            raise ValueError("Dados não processados. Execute process_raw_metrics primeiro.")
        
        if metric not in self.df.columns:
            raise ValueError(f"Métrica '{metric}' não encontrada nos dados")
        
        # Calcular z-score para cada container
        anomalies = []
        
        for container in self.df['container_name'].unique():
            container_data = self.df[self.df['container_name'] == container]
            mean_val = container_data[metric].mean()
            std_val = container_data[metric].std()
            
            if std_val > 0:
                z_scores = np.abs((container_data[metric] - mean_val) / std_val)
                anomaly_mask = z_scores > threshold_std
                
                if anomaly_mask.any():
                    anomaly_data = container_data[anomaly_mask].copy()
                    anomaly_data['z_score'] = z_scores[anomaly_mask]
                    anomalies.append(anomaly_data)
        
        if anomalies:
            return pd.concat(anomalies, ignore_index=True)
        else:
            return pd.DataFrame()