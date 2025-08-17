import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class DataExporter:
    """Exporta dados e gera visualizações"""
    
    def __init__(self, output_dir: str = "data/exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Configurar estilo dos gráficos
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def export_to_csv(self, df: pd.DataFrame, filename: str = None) -> str:
        """Exporta DataFrame para CSV"""
        if filename is None:
            filename = f"cadvisor_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"Dados exportados para: {filepath}")
        return filepath
    
    def export_to_json(self, data: Dict, filename: str = None) -> str:
        """Exporta dados para JSON"""
        if filename is None:
            filename = f"cadvisor_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Resumo exportado para: {filepath}")
        return filepath
    
    def create_resource_usage_charts(self, df: pd.DataFrame) -> str:
        """Cria gráficos de uso de recursos"""
        # Criar subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Uso de CPU', 'Uso de Memória', 'Tráfego de Rede', 'Uso de Disco'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": True}, {"secondary_y": False}]]
        )
        
        # Agrupar por container e calcular médias
        container_summary = df.groupby('container_name').agg({
            'cpu_total_usage': 'mean',
            'memory_usage_mb': 'mean',
            'network_rx_mb': 'sum',
            'network_tx_mb': 'sum',
            'filesystem_usage_gb': 'mean'
        }).reset_index()
        
        # Gráfico de CPU
        fig.add_trace(
            go.Bar(x=container_summary['container_name'], 
                   y=container_summary['cpu_total_usage'],
                   name='CPU Usage'),
            row=1, col=1
        )
        
        # Gráfico de Memória
        fig.add_trace(
            go.Bar(x=container_summary['container_name'], 
                   y=container_summary['memory_usage_mb'],
                   name='Memory (MB)'),
            row=1, col=2
        )
        
        # Gráfico de Rede
        fig.add_trace(
            go.Bar(x=container_summary['container_name'], 
                   y=container_summary['network_rx_mb'],
                   name='RX (MB)'),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=container_summary['container_name'], 
                   y=container_summary['network_tx_mb'],
                   name='TX (MB)'),
            row=2, col=1
        )
        
        # Gráfico de Disco
        fig.add_trace(
            go.Bar(x=container_summary['container_name'], 
                   y=container_summary['filesystem_usage_gb'],
                   name='Disk Usage (GB)'),
            row=2, col=2
        )
        
        fig.update_layout(height=800, title_text="Resumo de Uso de Recursos por Container")
        
        # Salvar gráfico
        filepath = os.path.join(self.output_dir, f"resource_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        fig.write_html(filepath)
        print(f"Gráfico de recursos salvo em: {filepath}")
        return filepath
    
    def create_timeline_charts(self, df: pd.DataFrame) -> str:
        """Cria gráficos de linha temporal"""
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('CPU ao Longo do Tempo', 'Memória ao Longo do Tempo', 'Rede ao Longo do Tempo'),
            shared_xaxes=True
        )
        
        # Selecionar containers principais (top 5 por uso de CPU)
        top_containers = (df.groupby('container_name')['cpu_total_usage']
                         .mean().sort_values(ascending=False).head(5).index)
        
        colors = px.colors.qualitative.Set1
        
        for i, container in enumerate(top_containers):
            container_data = df[df['container_name'] == container].sort_values('timestamp')
            color = colors[i % len(colors)]
            
            # CPU
            fig.add_trace(
                go.Scatter(x=container_data['timestamp'], 
                          y=container_data['cpu_total_usage'],
                          name=f'{container} - CPU',
                          line=dict(color=color)),
                row=1, col=1
            )
            
            # Memória
            fig.add_trace(
                go.Scatter(x=container_data['timestamp'], 
                          y=container_data['memory_usage_mb'],
                          name=f'{container} - Memory',
                          line=dict(color=color),
                          showlegend=False),
                row=2, col=1
            )
            
            # Rede (RX)
            fig.add_trace(
                go.Scatter(x=container_data['timestamp'], 
                          y=container_data['network_rx_mb'],
                          name=f'{container} - Network RX',
                          line=dict(color=color),
                          showlegend=False),
                row=3, col=1
            )
        
        fig.update_layout(height=900, title_text="Métricas ao Longo do Tempo (Top 5 Containers)")
        
        # Salvar gráfico
        filepath = os.path.join(self.output_dir, f"timeline_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        fig.write_html(filepath)
        print(f"Gráfico temporal salvo em: {filepath}")
        return filepath