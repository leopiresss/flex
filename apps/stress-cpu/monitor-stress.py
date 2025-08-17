#!/usr/bin/env python3
"""
Monitor de performance para o stress test
"""

import time
import subprocess
import json
from datetime import datetime

def get_pod_metrics():
    """Obtém métricas do pod via kubectl"""
    try:
        # CPU e Memory usage
        result = subprocess.run([
            'kubectl', 'top', 'pods', '-l', 'app=cpu-stress', 
            '--no-headers', '--use-protocol-buffers'
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    pod_name = parts[0]
                    cpu_usage = parts[1]
                    memory_usage = parts[2]
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'pod_name': pod_name,
                        'cpu_usage': cpu_usage,
                        'memory_usage': memory_usage
                    }
    except Exception as e:
        print(f"Erro ao obter métricas: {e}")
    
    return None

def monitor_loop(duration=300, interval=5):
    """Loop principal de monitoramento"""
    print(f"🔍 Iniciando monitoramento por {duration} segundos...")
    print(f"📊 Intervalo de coleta: {interval} segundos")
    print("-" * 60)
    
    start_time = time.time()
    
    while time.time() - start_time < duration:
        metrics = get_pod_metrics()
        if metrics:
            print(f"[{metrics['timestamp']}] "
                  f"Pod: {metrics['pod_name']} | "
                  f"CPU: {metrics['cpu_usage']} | "
                  f"Memory: {metrics['memory_usage']}")
        else:
            print(f"[{datetime.now().isoformat()}] Aguardando métricas...")
        
        time.sleep(interval)
    
    print("✅ Monitoramento finalizado")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de stress test')
    parser.add_argument('-d', '--duration', type=int, default=300,
                       help='Duração do monitoramento em segundos')
    parser.add_argument('-i', '--interval', type=int, default=5,
                       help='Intervalo entre coletas em segundos')
    
    args = parser.parse_args()
    monitor_loop(args.duration, args.interval)