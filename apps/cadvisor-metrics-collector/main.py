#!/usr/bin/env python3
"""
cAdvisor Metrics Collector
Programa principal para coletar e analisar métricas do cAdvisor em ambiente MicroK8s
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Adicionar diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

from cadvisor_client import CAdvisorClient
from metrics_processor import MetricsProcessor
from data_exporter import DataExporter
from dashboard import MetricsDashboard

def setup_logging():
    """Configura logging global"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'cadvisor_metrics_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='cAdvisor Metrics Collector')
    parser.add_argument('--config', default='config/config.yaml', help='Arquivo de configuração')
    parser.add_argument('--duration', type=int, default=60, help='Duração da coleta em minutos')
    parser.add_argument('--export-only', action='store_true', help='Apenas exportar dados sem dashboard')
    parser.add_argument('--dashboard-only', action='store_true', help='Apenas executar dashboard com dados existentes')
    parser.add_argument('--data-file', help='Arquivo CSV com dados para dashboard')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        if args.dashboard_only:
            if not args.data_file or not os.path.exists(args.data_file):
                logger.error("Para modo dashboard-only, especifique um arquivo de dados válido com --data-file")
                return 1
            
            import pandas as pd
            df = pd.read_csv(args.data_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            dashboard = MetricsDashboard(df)
            logger.info("Iniciando dashboard em http://localhost:8050")
            dashboard.run()
            return 0
        
        # Inicializar cliente cAdvisor
        logger.info("Inicializando cliente cAdvisor...")
        client = CAdvisorClient(args.config)
        
        # Testar conexão
        if not client.test_connection():
            logger.error("Não foi possível conectar ao cAdvisor. Verifique se está rodando em localhost:8080")
            return 1
        
        # Obter informações da máquina
        machine_info = client.get_machine_info()
        logger.info(f"Máquina detectada: {machine_info.get('num_cores', 'N/A')} CPUs, "
                   f"{machine_info.get('memory_capacity', 0) / (1024**3):.2f} GB RAM")
        
        # Coletar métricas
        logger.info(f"Iniciando coleta de métricas por {args.duration} minutos...")
        raw_metrics = client.collect_metrics_continuously(args.duration)
        
        if not raw_metrics:
            logger.error("Nenhuma métrica foi coletada")
            return 1
        
        # Processar métricas
        logger.info("Processando métricas...")
        processor = MetricsProcessor()
        df = processor.process_raw_metrics(raw_metrics)
        df_with_cpu = processor.calculate_cpu_percentage(machine_info)
        
        # Gerar estatísticas
        summary = processor.get_summary_statistics()
        logger.info(f"Processados dados de {summary['total_containers']} containers")
        
        # Exportar dados
        logger.info("Exportando dados...")
        exporter = DataExporter()
        
        # Exportar CSV
        csv_file = exporter.export_to_csv(df_with_cpu)
        
        # Exportar resumo JSON
        json_file = exporter.export_to_json(summary)
        
        # Criar gráficos
        resource_chart = exporter.create_resource_usage_charts(df_with_cpu)
        timeline_chart = exporter.create_timeline_charts(df_with_cpu)
        
        # Detectar anomalias
        anomalies = processor.detect_anomalies('memory_usage_mb')
        if not anomalies.empty:
            logger.info(f"Detectadas {len(anomalies)} anomalias de memória")
            anomaly_file = exporter.export_to_csv(anomalies, "memory_anomalies.csv")
        
        # Top consumers
        top_cpu = processor.get_top_consumers('cpu_total_usage')
        top_memory = processor.get_top_consumers('memory_usage_mb')
        
        logger.info("Top 5 consumidores de CPU:")
        print(top_cpu)
        
        logger.info("Top 5 consumidores de Memória:")
        print(top_memory)
        
        if not args.export_only:
            # Iniciar dashboard
            logger.info("Iniciando dashboard interativo em http://localhost:8050")
            dashboard = MetricsDashboard(df_with_cpu)
            dashboard.run()
        
        logger.info("Coleta e análise concluídas com sucesso!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operação cancelada pelo usuário")
        return 0
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())