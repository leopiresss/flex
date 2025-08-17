#!/usr/bin/env python3
"""
Memory Stress Test complementar ao CPU stress
"""

import time
import argparse
import signal
import sys
import gc
from datetime import datetime

class MemoryStresser:
    def __init__(self, size_mb=100, duration=60, pattern='random'):
        self.size_mb = size_mb
        self.duration = duration
        self.pattern = pattern
        self.memory_blocks = []
        self.running = True
        
    def signal_handler(self, signum, frame):
        print(f"\n[{datetime.now()}] Parando memory stress test...")
        self.cleanup()
        sys.exit(0)
    
    def allocate_memory(self):
        """Aloca blocos de memória"""
        try:
            if self.pattern == 'sequential':
                # Padrão sequencial
                data = list(range(self.size_mb * 1024 * 256))  # ~1MB por 256k integers
            elif self.pattern == 'random':
                # Padrão aleatório
                import random
                data = [random.randint(0, 1000000) for _ in range(self.size_mb * 1024 * 256)]
            else:
                # Padrão zero
                data = [0] * (self.size_mb * 1024 * 256)
            
            self.memory_blocks.append(data)
            return True
        except MemoryError:
            print(f"[{datetime.now()}] Limite de memória atingido")
            return False
    
    def start(self):
        """Inicia o stress test de memória"""
        print(f"[{datetime.now()}] Iniciando Memory Stress Test")
        print(f"Tamanho alvo: {self.size_mb}MB")
        print(f"Duração: {self.duration}s")
        print(f"Padrão: {self.pattern}")
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        start_time = time.time()
        allocated_mb = 0
        
        try:
            while self.running and (time.time() - start_time) < self.duration:
                if self.allocate_memory():
                    allocated_mb += self.size_mb
                    print(f"[{datetime.now()}] Alocado: {allocated_mb}MB")
                    time.sleep(1)
                else:
                    break
            
            # Mantém memória alocada pelo resto da duração
            remaining_time = self.duration - (time.time() - start_time)
            if remaining_time > 0:
                print(f"[{datetime.now()}] Mantendo {allocated_mb}MB alocados por {remaining_time:.1f}s")
                time.sleep(remaining_time)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Libera memória alocada"""
        print(f"[{datetime.now()}] Liberando memória...")
        self.memory_blocks.clear()
        gc.collect()
        print(f"[{datetime.now()}] Memory Stress Test finalizado")

def main():
    parser = argparse.ArgumentParser(description='Memory Stress Test')
    parser.add_argument('-s', '--size', type=int, default=100,
                       help='Tamanho em MB para alocar (default: 100)')
    parser.add_argument('-d', '--duration', type=int, default=60,
                       help='Duração em segundos (default: 60)')
    parser.add_argument('-p', '--pattern', choices=['random', 'sequential', 'zero'],
                       default='random', help='Padrão de dados (default: random)')
    
    args = parser.parse_args()
    
    stresser = MemoryStresser(
        size_mb=args.size,
        duration=args.duration,
        pattern=args.pattern
    )
    
    stresser.start()

if __name__ == "__main__":
    main()