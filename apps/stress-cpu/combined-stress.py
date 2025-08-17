#!/usr/bin/env python3
"""
Stress Test combinado: CPU + Memória + I/O
"""

import multiprocessing
import threading
import time
import argparse
import signal
import sys
import os
import tempfile
from datetime import datetime

class CombinedStresser:
    def __init__(self, duration=60, cpu_cores=None, memory_mb=100, io_workers=2):
        self.duration = duration
        self.cpu_cores = cpu_cores or multiprocessing.cpu_count()
        self.memory_mb = memory_mb
        self.io_workers = io_workers
        self.running = True
        self.processes = []
        self.threads = []
        self.memory_blocks = []
        
    def cpu_worker(self, worker_id):
        """Worker de CPU stress"""
        print(f"[{datetime.now()}] CPU Worker {worker_id} iniciado")
        while self.running:
            # Operações intensivas de CPU
            _ = sum(i * i * i for i in range(10000))
    
    def memory_worker(self):
        """Worker de Memory stress"""
        print(f"[{datetime.now()}] Memory Worker iniciado")
        try:
            while self.running and len(self.memory_blocks) * 10 < self.memory_mb:
                # Aloca blocos de ~10MB
                data = [0] * (10 * 1024 * 256)
                self.memory_blocks.append(data)
                time.sleep(0.1)
        except MemoryError:
            print(f"[{datetime.now()}] Limite de memória atingido")
    
    def io_worker(self, worker_id):
        """Worker de I/O stress"""
        print(f"[{datetime.now()}] I/O Worker {worker_id} iniciado")
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            while self.running:
                # Escreve dados
                data = b"0" * 1024 * 1024  # 1MB
                temp_file.write(data)
                temp_file.flush()
                os.fsync(temp_file.fileno())
                
                # Lê dados
                temp_file.seek(0)
                _ = temp_file.read()
                time.sleep(0.1)
        except Exception as e:
            print(f"[{datetime.now()}] Erro I/O Worker {worker_id}: {e}")
        finally:
            if temp_file:
                temp_file.close()
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
    
    def signal_handler(self, signum, frame):
        """Handler para parada graceful"""
        print(f"\n[{datetime.now()}] Parando Combined Stress Test...")
        self.running = False
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Inicia todos os stress tests"""
        print(f"[{datetime.now()}] Iniciando Combined Stress Test")
        print(f"CPU Cores: {self.cpu_cores}")
        print(f"Memória: {self.memory_mb}MB")
        print(f"I/O Workers: {self.io_workers}")
        print(f"Duração: {self.duration}s")
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Inicia CPU workers
        for i in range(self.cpu_cores):
            process = multiprocessing.Process(target=self.cpu_worker, args=(i,))
            process.start()
            self.processes.append(process)
        
        # Inicia Memory worker
        memory_thread = threading.Thread(target=self.memory_worker)
        memory_thread.start()
        self.threads.append(memory_thread)
        
        # Inicia I/O workers
        for i in range(self.io_workers):
            io_thread = threading.Thread(target=self.io_worker, args=(i,))
            io_thread.start()
            self.threads.append(io_thread)
        
        # Aguarda duração
        try:
            time.sleep(self.duration)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self):
        """Para todos os workers"""
        self.running = False
        
        # Para processos CPU
        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        
        # Para threads
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        # Libera memória
        self.memory_blocks.clear()
        print(f"[{datetime.now()}] Combined Stress Test finalizado")

def main():
    parser = argparse.ArgumentParser(description='Combined Stress Test')
    parser.add_argument('-d', '--duration', type=int, default=60)
    parser.add_argument('-c', '--cpu-cores', type=int, default=None)
    parser.add_argument('-m', '--memory', type=int, default=100)
    parser.add_argument('-i', '--io-workers', type=int, default=2)
    
    args = parser.parse_args()
    
    stresser = CombinedStresser(
        duration=args.duration,
        cpu_cores=args.cpu_cores,
        memory_mb=args.memory,
        io_workers=args.io_workers
    )
    
    stresser.start()

if __name__ == "__main__":
    main()