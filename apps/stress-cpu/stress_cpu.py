#!/usr/bin/env python3
"""
CPU Stress Test para ambiente Kubernetes
Programa para gerar carga de CPU controlada em pods
"""

import multiprocessing
import time
import argparse
import signal
import sys
import os
from datetime import datetime

class CPUStresser:
    def __init__(self, duration=60, cpu_cores=None, intensity=100):
        self.duration = duration
        self.cpu_cores = cpu_cores or multiprocessing.cpu_count()
        self.intensity = intensity / 100.0
        self.processes = []
        self.running = True
        
    def cpu_stress_worker(self, worker_id):
        """Worker que executa o stress de CPU"""
        print(f"[{datetime.now()}] Worker {worker_id} iniciado")
        
        while self.running:
            # Período de trabalho intensivo
            start_time = time.time()
            while (time.time() - start_time) < self.intensity:
                # Operação que consome CPU
                _ = sum(i * i for i in range(1000))
            
            # Período de descanso se intensity < 100%
            if self.intensity < 1.0:
                time.sleep(1.0 - self.intensity)
    
    def signal_handler(self, signum, frame):
        """Handler para interrupção graceful"""
        print(f"\n[{datetime.now()}] Recebido sinal {signum}. Parando stress test...")
        self.running = False
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Inicia o stress test"""
        print(f"[{datetime.now()}] Iniciando CPU Stress Test")
        print(f"Cores: {self.cpu_cores}")
        print(f"Duração: {self.duration}s")
        print(f"Intensidade: {int(self.intensity * 100)}%")
        print(f"PID: {os.getpid()}")
        
        # Registra handlers para sinais
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Cria processos workers
        for i in range(self.cpu_cores):
            process = multiprocessing.Process(
                target=self.cpu_stress_worker,
                args=(i,)
            )
            process.start()
            self.processes.append(process)
        
        # Aguarda duração especificada
        try:
            time.sleep(self.duration)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self):
        """Para todos os processos workers"""
        self.running = False
        print(f"[{datetime.now()}] Parando workers...")
        
        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
        
        print(f"[{datetime.now()}] CPU Stress Test finalizado")

def main():
    parser = argparse.ArgumentParser(description='CPU Stress Test para Kubernetes')
    parser.add_argument('-d', '--duration', type=int, default=60,
                       help='Duração do teste em segundos (default: 60)')
    parser.add_argument('-c', '--cores', type=int, default=None,
                       help='Número de cores para usar (default: todos)')
    parser.add_argument('-i', '--intensity', type=int, default=100,
                       help='Intensidade do stress 1-100%% (default: 100)')
    
    args = parser.parse_args()
    
    # Validações
    if args.intensity < 1 or args.intensity > 100:
        print("Erro: Intensidade deve estar entre 1 e 100")
        sys.exit(1)
    
    if args.cores and args.cores < 1:
        print("Erro: Número de cores deve ser maior que 0")
        sys.exit(1)
    
    # Inicia stress test
    stresser = CPUStresser(
        duration=args.duration,
        cpu_cores=args.cores,
        intensity=args.intensity
    )
    
    stresser.start()

if __name__ == "__main__":
    main()