import os
import time
import logging
import random
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Node:
    """Nó da árvore binária para consumo de memória"""
    def __init__(self, value, data_size=1024):
        self.value = value
        self.left = None
        self.right = None
        # Aloca memória adicional com dados simulados
        self.data = bytearray(data_size)
        
class BinaryTreeMemoryStress:
    """Classe para stress test de memória usando árvore binária"""
    
    def __init__(self, target_mb=100, node_size_kb=1, duration_seconds=300):
        self.target_mb = target_mb
        self.node_size_bytes = node_size_kb * 1024
        self.duration_seconds = duration_seconds
        self.root = None
        self.node_count = 0
        self.all_nodes = []  # Lista para manter referências
        
    def insert_iterative(self, value):
        """Insere um nó na árvore de forma iterativa (evita recursão)"""
        new_node = Node(value, self.node_size_bytes)
        self.all_nodes.append(new_node)  # Mantém referência
        self.node_count += 1
        
        if self.root is None:
            self.root = new_node
            return
        
        current = self.root
        while True:
            if value < current.value:
                if current.left is None:
                    current.left = new_node
                    break
                current = current.left
            else:
                if current.right is None:
                    current.right = new_node
                    break
                current = current.right
    
    def calculate_nodes_needed(self):
        """Calcula quantos nós são necessários para atingir o target"""
        target_bytes = self.target_mb * 1024 * 1024
        nodes_needed = target_bytes // self.node_size_bytes
        return nodes_needed
    
    def build_tree(self):
        """Constrói a árvore até atingir o consumo de memória desejado"""
        nodes_needed = self.calculate_nodes_needed()
        logging.info(f"Iniciando construção da árvore. Target: {self.target_mb}MB")
        logging.info(f"Nós necessários: {nodes_needed}")
        
        # Gerar valores aleatórios para melhor balanceamento
        logging.info("Gerando valores aleatórios para balanceamento...")
        values = list(range(nodes_needed))
        random.shuffle(values)
        
        start_time = time.time()
        
        for i, value in enumerate(values):
            self.insert_iterative(value)
            
            if (i + 1) % 10000 == 0:
                elapsed = time.time() - start_time
                mb_allocated = (i + 1) * self.node_size_bytes / (1024 * 1024)
                logging.info(f"Nós criados: {i + 1}/{nodes_needed} | "
                           f"Memória alocada: {mb_allocated:.2f}MB | "
                           f"Tempo: {elapsed:.2f}s")
        
        total_time = time.time() - start_time
        final_mb = self.node_count * self.node_size_bytes / (1024 * 1024)
        logging.info(f"Árvore construída! Total de nós: {self.node_count}")
        logging.info(f"Memória total alocada: {final_mb:.2f}MB")
        logging.info(f"Tempo total de construção: {total_time:.2f}s")
    
    def traverse_tree_iterative(self):
        """Percorre a árvore iterativamente (evita recursão)"""
        if self.root is None:
            return 0
        
        count = 0
        stack = [self.root]
        
        while stack:
            node = stack.pop()
            count += 1
            
            # Acessa os dados para evitar otimizações do garbage collector
            if len(node.data) > 0:
                _ = node.data[0]
            
            if node.right:
                stack.append(node.right)
            if node.left:
                stack.append(node.left)
        
        return count
    
    def access_random_nodes(self, sample_size=1000):
        """Acessa nós aleatórios para manter dados ativos na memória"""
        if len(self.all_nodes) == 0:
            return 0
        
        sample_size = min(sample_size, len(self.all_nodes))
        sampled_nodes = random.sample(self.all_nodes, sample_size)
        
        accessed = 0
        for node in sampled_nodes:
            # Acessa e modifica dados para garantir que estejam na memória
            if len(node.data) > 10:
                node.data[0] = (node.data[0] + 1) % 256
                node.data[-1] = (node.data[-1] + 1) % 256
                accessed += 1
        
        return accessed
    
    def maintain_pressure(self):
        """Mantém pressão de memória pelo tempo especificado"""
        logging.info(f"Mantendo pressão de memória por {self.duration_seconds} segundos...")
        
        end_time = time.time() + self.duration_seconds
        iteration = 0
        
        while time.time() < end_time:
            iteration += 1
            remaining = int(end_time - time.time())
            
            # Alterna entre travessia completa e acesso aleatório
            if iteration % 2 == 0:
                nodes_visited = self.traverse_tree_iterative()
                action = "Travessia completa"
            else:
                nodes_visited = self.access_random_nodes(5000)
                action = "Acesso aleatório"
            
            mb_used = self.node_count * self.node_size_bytes / (1024 * 1024)
            
            logging.info(f"Iteração {iteration} | {action} | "
                       f"Nós acessados: {nodes_visited} | "
                       f"Memória: {mb_used:.2f}MB | "
                       f"Tempo restante: {remaining}s")
            
            time.sleep(10)
        
        logging.info("Teste de stress concluído!")
    
    def run(self):
        """Executa o teste de stress completo"""
        logging.info("=" * 60)
        logging.info("INICIANDO TESTE DE STRESS DE MEMÓRIA")
        logging.info("=" * 60)
        logging.info(f"Configuração:")
        logging.info(f"  - Target de memória: {self.target_mb}MB")
        logging.info(f"  - Tamanho do nó: {self.node_size_bytes / 1024}KB")
        logging.info(f"  - Duração: {self.duration_seconds}s")
        logging.info("=" * 60)
        
        try:
            self.build_tree()
            self.maintain_pressure()
        except MemoryError:
            logging.error("MemoryError: Limite de memória atingido!")
            logging.error(f"Nós criados antes do erro: {self.node_count}")
            mb_allocated = self.node_count * self.node_size_bytes / (1024 * 1024)
            logging.error(f"Memória alocada: {mb_allocated:.2f}MB")
            raise
        except Exception as e:
            logging.error(f"Erro durante execução: {e}")
            raise
        finally:
            logging.info("Encerrando aplicação...")

if __name__ == "__main__":
    # Configurações via variáveis de ambiente
    target_mb = int(os.getenv("MEMORY_TARGET_MB", "500"))
    node_size_kb = int(os.getenv("NODE_SIZE_KB", "1"))
    #duration_seconds = int(os.getenv("DURATION_SECONDS", "3600"))
    duration_seconds = int(os.getenv("DURATION_SECONDS", "120"))
    
    stress_test = BinaryTreeMemoryStress(
        target_mb=target_mb,
        node_size_kb=node_size_kb,
        duration_seconds=duration_seconds
    )
    
    stress_test.run()