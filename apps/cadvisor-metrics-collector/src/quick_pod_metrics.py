#!/usr/bin/env python3

from pod_metrics_collector import PodMetricsCollector
import sys

def main():
  #  if len(sys.argv) < 2:
  #      print("Uso: python quick_pod_metrics.py <nome_do_pod>")
  #      print("Exemplo: python quick_pod_metrics.py cpu-stress-job-l9rxd")
  #      sys.exit(1)
    
    # pod_name = sys.argv[1]
    pod_name = 'cpu-stress-job-l9rxd'
    
    print(f"🚀 Coletando métricas do pod: {pod_name}")
    print("=" * 50)
    
    # Criar coletor
    collector = PodMetricsCollector()
    
    # Testar conexão
    if not collector.test_connection():
        print("❌ Erro: cAdvisor não acessível em localhost:8080")
        print("Execute: microk8s kubectl port-forward -n monitoring svc/cadvisor 8080:8080")
        sys.exit(1)
    
    # Coletar métricas
    metrics = collector.collect_pod_metrics(pod_name)
    
    if metrics:
        collector.print_metrics_summary(metrics)
        
        # Salvar em CSV
        df = collector.metrics_to_dataframe(metrics)
        filename = f"{pod_name}_metrics.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Métricas salvas em: {filename}")
    else:
        print(f"❌ Pod '{pod_name}' não encontrado")

if __name__ == "__main__":
    main()