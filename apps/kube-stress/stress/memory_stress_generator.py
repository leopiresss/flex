"""
Gerador de Stress de Memória para Kubernetes
Autor: Sistema de Testes
Descrição: Gera carga controlada de memória e CPU para testes de ML
"""

import time
import sys
import os
import random
import argparse
import logging
from datetime import datetime
from typing import List, Dict
import psutil
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryStressGenerator:
    """Gerador de stress de memória controlado"""
    
    def __init__(self, max_memory_mb: int = 500):
        """
        Inicializa o gerador de stress
        
        Args:
            max_memory_mb: Memória máxima a alocar em MB
        """
        self.max_memory_mb = max_memory_mb
        self.memory_blocks = []
        self.is_running = False
        self.current_memory_mb = 0
        
        logger.info(f"🎯 Gerador de Stress inicializado (max: {max_memory_mb} MB)")
    
    def allocate_memory(self, size_mb: int):
        """Aloca bloco de memória"""
        try:
            # Aloca array de bytes
            block_size = size_mb * 1024 * 1024
            memory_block = bytearray(block_size)
            
            # Preenche com dados aleatórios para garantir alocação real
            for i in range(0, block_size, 1024):
                memory_block[i] = random.randint(0, 255)
            
            self.memory_blocks.append(memory_block)
            self.current_memory_mb += size_mb
            
            logger.info(f"✅ Alocados {size_mb} MB | Total: {self.current_memory_mb} MB")
            return True
        except MemoryError:
            logger.error(f"❌ Erro ao alocar {size_mb} MB - Memória insuficiente")
            return False
    
    def release_memory(self, size_mb: int):
        """Libera bloco de memória"""
        released = 0
        while self.memory_blocks and released < size_mb:
            block = self.memory_blocks.pop()
            block_size_mb = len(block) // (1024 * 1024)
            released += block_size_mb
            del block
        
        self.current_memory_mb = max(0, self.current_memory_mb - released)
        logger.info(f"🗑️  Liberados {released} MB | Total: {self.current_memory_mb} MB")
    
    def release_all_memory(self):
        """Libera toda memória alocada"""
        self.memory_blocks.clear()
        self.current_memory_mb = 0
        logger.info("🗑️  Toda memória liberada")
    
    def get_system_memory_info(self) -> Dict:
        """Retorna informações de memória do sistema"""
        mem = psutil.virtual_memory()
        return {
            'total_mb': mem.total / (1024 * 1024),
            'available_mb': mem.available / (1024 * 1024),
            'used_mb': mem.used / (1024 * 1024),
            'percent': mem.percent,
            'allocated_by_script_mb': self.current_memory_mb
        }
    
    def print_memory_status(self):
        """Imprime status da memória"""
        info = self.get_system_memory_info()
        logger.info(f"📊 Memória do Sistema: {info['used_mb']:.0f}/{info['total_mb']:.0f} MB ({info['percent']:.1f}%)")
        logger.info(f"📊 Alocado pelo script: {info['allocated_by_script_mb']} MB")


class CPUStressGenerator:
    """Gerador de stress de CPU"""
    
    def __init__(self, num_threads: int = 2):
        """
        Inicializa gerador de stress de CPU
        
        Args:
            num_threads: Número de threads para gerar carga
        """
        self.num_threads = num_threads
        self.is_running = False
        self.threads = []
        
        logger.info(f"🎯 Gerador de CPU Stress inicializado ({num_threads} threads)")
    
    def _cpu_intensive_task(self, thread_id: int, duration: int):
        """Tarefa intensiva de CPU"""
        logger.info(f"🔥 Thread {thread_id} iniciada")
        start_time = time.time()
        
        while time.time() - start_time < duration and self.is_running:
            # Operações matemáticas intensivas
            result = 0
            for i in range(10000):
                result += i ** 2
                result = result % 1000000
        
        logger.info(f"✅ Thread {thread_id} finalizada")
    
    def start_stress(self, duration: int = 60):
        """
        Inicia stress de CPU
        
        Args:
            duration: Duração em segundos
        """
        self.is_running = True
        self.threads = []
        
        for i in range(self.num_threads):
            thread = threading.Thread(
                target=self._cpu_intensive_task,
                args=(i, duration)
            )
            thread.start()
            self.threads.append(thread)
        
        logger.info(f"🔥 CPU Stress iniciado ({self.num_threads} threads por {duration}s)")
    
    def stop_stress(self):
        """Para o stress de CPU"""
        self.is_running = False
        for thread in self.threads:
            thread.join(timeout=5)
        logger.info("⏹️  CPU Stress parado")


class StressScenarioExecutor:
    """Executor de cenários de stress predefinidos"""
    
    def __init__(self, memory_generator: MemoryStressGenerator,
                 cpu_generator: CPUStressGenerator):
        self.memory = memory_generator
        self.cpu = cpu_generator
    
    def scenario_gradual_increase(self, max_memory_mb: int = 500, 
                                  step_mb: int = 50, interval_seconds: int = 30):
        """
        Cenário: Aumento gradual de memória
        Simula crescimento linear de uso
        """
        logger.info("\n" + "="*60)
        logger.info("📈 CENÁRIO: AUMENTO GRADUAL DE MEMÓRIA")
        logger.info("="*60)
        
        current = 0
        while current < max_memory_mb:
            self.memory.allocate_memory(step_mb)
            self.memory.print_memory_status()
            current += step_mb
            
            if current < max_memory_mb:
                logger.info(f"⏳ Aguardando {interval_seconds}s...")
                time.sleep(interval_seconds)
        
        logger.info("✅ Cenário concluído - Memória no máximo")
    
    def scenario_spike_pattern(self, spike_mb: int = 300, 
                               base_mb: int = 100, cycles: int = 5,
                               spike_duration: int = 60, rest_duration: int = 120):
        """
        Cenário: Picos de memória
        Simula padrão de spikes periódicos
        """
        logger.info("\n" + "="*60)
        logger.info("⚡ CENÁRIO: PICOS DE MEMÓRIA")
        logger.info("="*60)
        
        for cycle in range(cycles):
            logger.info(f"\n🔄 Ciclo {cycle + 1}/{cycles}")
            
            # Aloca memória base
            logger.info(f"📊 Alocando memória base: {base_mb} MB")
            self.memory.allocate_memory(base_mb)
            self.memory.print_memory_status()
            
            # Pico de memória
            logger.info(f"⚡ PICO: Alocando {spike_mb} MB adicional")
            self.memory.allocate_memory(spike_mb)
            self.memory.print_memory_status()
            
            logger.info(f"⏳ Mantendo pico por {spike_duration}s...")
            time.sleep(spike_duration)
            
            # Libera pico
            logger.info(f"📉 Liberando pico de memória")
            self.memory.release_memory(spike_mb)
            self.memory.print_memory_status()
            
            if cycle < cycles - 1:
                logger.info(f"⏳ Período de descanso: {rest_duration}s...")
                time.sleep(rest_duration)
                self.memory.release_all_memory()
        
        logger.info("✅ Cenário concluído")
    
    def scenario_random_load(self, duration_minutes: int = 30, 
                            min_mb: int = 50, max_mb: int = 400,
                            change_interval: int = 45):
        """
        Cenário: Carga aleatória
        Simula comportamento imprevisível
        """
        logger.info("\n" + "="*60)
        logger.info("🎲 CENÁRIO: CARGA ALEATÓRIA")
        logger.info("="*60)
        
        start_time = time.time()
        duration_seconds = duration_minutes * 60
        
        while time.time() - start_time < duration_seconds:
            # Libera memória atual
            self.memory.release_all_memory()
            
            # Aloca quantidade aleatória
            random_mb = random.randint(min_mb, max_mb)
            logger.info(f"🎲 Alocando {random_mb} MB aleatoriamente")
            self.memory.allocate_memory(random_mb)
            self.memory.print_memory_status()
            
            # Aguarda intervalo
            logger.info(f"⏳ Aguardando {change_interval}s...")
            time.sleep(change_interval)
        
        logger.info("✅ Cenário concluído")
    
    def scenario_stress_test(self, target_mb: int = 600, 
                            duration_minutes: int = 10):
        """
        Cenário: Teste de stress
        Mantém memória alta + CPU alto
        """
        logger.info("\n" + "="*60)
        logger.info("💥 CENÁRIO: TESTE DE STRESS COMPLETO")
        logger.info("="*60)
        
        # Aloca memória
        logger.info(f"📊 Alocando {target_mb} MB")
        self.memory.allocate_memory(target_mb)
        self.memory.print_memory_status()
        
        # Inicia stress de CPU
        duration_seconds = duration_minutes * 60
        logger.info(f"🔥 Iniciando stress de CPU por {duration_minutes} minutos")
        self.cpu.start_stress(duration_seconds)
        
        # Monitora durante execução
        for i in range(duration_minutes):
            time.sleep(60)
            logger.info(f"⏱️  {i+1}/{duration_minutes} minutos decorridos")
            self.memory.print_memory_status()
        
        # Finaliza
        self.cpu.stop_stress()
        logger.info("✅ Cenário concluído")
    
    def scenario_memory_leak_simulation(self, leak_rate_mb: int = 10,
                                       interval_seconds: int = 30,
                                       max_memory_mb: int = 500):
        """
        Cenário: Simulação de memory leak
        Aumenta memória constantemente sem liberar
        """
        logger.info("\n" + "="*60)
        logger.info("💧 CENÁRIO: SIMULAÇÃO DE MEMORY LEAK")
        logger.info("="*60)
        
        current = 0
        iteration = 0
        
        while current < max_memory_mb:
            iteration += 1
            logger.info(f"\n💧 Leak #{iteration}: Alocando {leak_rate_mb} MB (sem liberar)")
            self.memory.allocate_memory(leak_rate_mb)
            current += leak_rate_mb
            
            self.memory.print_memory_status()
            
            if current < max_memory_mb:
                logger.info(f"⏳ Aguardando {interval_seconds}s...")
                time.sleep(interval_seconds)
        
        logger.info("⚠️  Limite de memória atingido!")
        logger.info("✅ Cenário concluído")
    
    def scenario_oscillating_load(self, duration_minutes: int = 20,
                                  low_mb: int = 100, high_mb: int = 400,
                                  cycle_duration: int = 120):
        """
        Cenário: Carga oscilante
        Alterna entre uso baixo e alto
        """
        logger.info("\n" + "="*60)
        logger.info("🌊 CENÁRIO: CARGA OSCILANTE")
        logger.info("="*60)
        
        start_time = time.time()
        duration_seconds = duration_minutes * 60
        cycle = 0
        
        while time.time() - start_time < duration_seconds:
            cycle += 1
            is_high = cycle % 2 == 1
            
            # Limpa memória anterior
            self.memory.release_all_memory()
            
            if is_high:
                logger.info(f"📈 Ciclo {cycle}: Carga ALTA ({high_mb} MB)")
                self.memory.allocate_memory(high_mb)
            else:
                logger.info(f"📉 Ciclo {cycle}: Carga BAIXA ({low_mb} MB)")
                self.memory.allocate_memory(low_mb)
            
            self.memory.print_memory_status()
            
            logger.info(f"⏳ Mantendo por {cycle_duration}s...")
            time.sleep(cycle_duration)
        
        logger.info("✅ Cenário concluído")


def main():
    parser = argparse.ArgumentParser(
        description='Gerador de Stress de Memória e CPU para Kubernetes'
    )
    
    parser.add_argument('--scenario', type=str, default='gradual',
                       choices=['gradual', 'spike', 'random', 'stress', 
                               'leak', 'oscillating', 'custom'],
                       help='Cenário de stress a executar')
    
    parser.add_argument('--max-memory', type=int, default=500,
                       help='Memória máxima em MB (default: 500)')
    
    parser.add_argument('--duration', type=int, default=30,
                       help='Duração em minutos (default: 30)')
    
    parser.add_argument('--cpu-threads', type=int, default=2,
                       help='Número de threads de CPU (default: 2)')
    
    parser.add_argument('--interval', type=int, default=30,
                       help='Intervalo entre mudanças em segundos (default: 30)')
    
    args = parser.parse_args()
    
    # Inicializa geradores
    memory_gen = MemoryStressGenerator(max_memory_mb=args.max_memory)
    cpu_gen = CPUStressGenerator(num_threads=args.cpu_threads)
    executor = StressScenarioExecutor(memory_gen, cpu_gen)
    
    try:
        logger.info("\n" + "="*70)
        logger.info("🚀 INICIANDO GERADOR DE STRESS")
        logger.info("="*70)
        logger.info(f"Cenário: {args.scenario}")
        logger.info(f"Memória máxima: {args.max_memory} MB")
        logger.info(f"Duração: {args.duration} minutos")
        logger.info(f"Threads CPU: {args.cpu_threads}")
        logger.info("="*70 + "\n")
        
        # Executa cenário escolhido
        if args.scenario == 'gradual':
            executor.scenario_gradual_increase(
                max_memory_mb=args.max_memory,
                interval_seconds=args.interval
            )
        
        elif args.scenario == 'spike':
            executor.scenario_spike_pattern(
                spike_mb=int(args.max_memory * 0.6),
                base_mb=int(args.max_memory * 0.2),
                cycles=5
            )
        
        elif args.scenario == 'random':
            executor.scenario_random_load(
                duration_minutes=args.duration,
                max_mb=args.max_memory,
                change_interval=args.interval
            )
        
        elif args.scenario == 'stress':
            executor.scenario_stress_test(
                target_mb=args.max_memory,
                duration_minutes=args.duration
            )
        
        elif args.scenario == 'leak':
            executor.scenario_memory_leak_simulation(
                leak_rate_mb=20,
                max_memory_mb=args.max_memory,
                interval_seconds=args.interval
            )
        
        elif args.scenario == 'oscillating':
            executor.scenario_oscillating_load(
                duration_minutes=args.duration,
                low_mb=int(args.max_memory * 0.2),
                high_mb=int(args.max_memory * 0.8)
            )
        
        elif args.scenario == 'custom':
            # Cenário customizado - pode ser personalizado
            logger.info("Executando cenário customizado...")
            memory_gen.allocate_memory(args.max_memory)
            time.sleep(args.duration * 60)
        
        logger.info("\n" + "="*70)
        logger.info("✅ EXECUÇÃO FINALIZADA COM SUCESSO")
        logger.info("="*70)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrompido pelo usuário")
    
    except Exception as e:
        logger.error(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpeza
        logger.info("\n🧹 Liberando recursos...")
        memory_gen.release_all_memory()
        cpu_gen.stop_stress()
        logger.info("✅ Recursos liberados")


if __name__ == "__main__":
    main()