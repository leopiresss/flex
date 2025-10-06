#!/usr/bin/env python3
"""
Aplicação de Stress Test de Memória para Kubernetes
Utiliza árvore binária para consumo controlado de memória
"""

import threading
import time
import psutil
import os
from datetime import datetime
from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Classe do Nó da Árvore Binária
class TreeNode:
    def __init__(self, value, payload_size_kb=100):
        self.value = value
        self.left = None
        self.right = None
        # Payload para consumir memória (em KB)
        self.data = bytearray(payload_size_kb * 1024)
    
    def insert(self, value, payload_size_kb=100):
        """Insere um valor na árvore binária"""
        if value < self.value:
            if self.left is None:
                self.left = TreeNode(value, payload_size_kb)
            else:
                self.left.insert(value, payload_size_kb)
        else:
            if self.right is None:
                self.right = TreeNode(value, payload_size_kb)
            else:
                self.right.insert(value, payload_size_kb)
    
    def search(self, value):
        """Pesquisa um valor na árvore"""
        if value == self.value:
            return True
        elif value < self.value and self.left:
            return self.left.search(value)
        elif value > self.value and self.right:
            return self.right.search(value)
        return False
    
    def count_nodes(self):
        """Conta o número de nós na árvore"""
        count = 1
        if self.left:
            count += self.left.count_nodes()
        if self.right:
            count += self.right.count_nodes()
        return count


# Classe para gerenciar o Stress Test
class StressTestManager:
    def __init__(self):
        self.root = None
        self.logs = []
        self.is_running = False
        self.stop_flag = False
        self.lock = threading.Lock()
        self.config = {
            'memory_mb': 100,
            'duration_seconds': 60,
            'log_interval_sec': 5
        }
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage_mb(self):
        """Retorna o uso de memória em MB"""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def add_log(self, operation, message=""):
        """Adiciona uma entrada no log"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'memory_use_mb': round(self.get_memory_usage_mb(), 2),
            'message': message
        }
        with self.lock:
            self.logs.append(log_entry)
        print(f"[{log_entry['timestamp']}] {operation} - {log_entry['memory_use_mb']} MB - {message}")
    
    def build_tree_routine(self, target_memory_mb, payload_size_kb):
        """Rotina 1: Constrói a árvore binária até atingir o consumo de memória alvo"""
        self.add_log("BUILD_TREE_START", f"Iniciando construção da árvore. Alvo: {target_memory_mb} MB")
        
        # Inicializa a árvore com o nó raiz
        self.root = TreeNode(random.randint(1, 1000000), payload_size_kb)
        node_count = 1
        
        while not self.stop_flag:
            current_memory = self.get_memory_usage_mb()
            
            if current_memory >= target_memory_mb:
                self.add_log("BUILD_TREE_TARGET", f"Memória alvo atingida com {node_count} nós")
                break
            
            # Insere novos nós
            for _ in range(10):  # Insere em lotes para melhor performance
                if current_memory >= target_memory_mb or self.stop_flag:
                    break
                value = random.randint(1, 1000000)
                self.root.insert(value, payload_size_kb)
                node_count += 1
            
            time.sleep(0.01)  # Pequena pausa para não sobrecarregar
        
        if not self.stop_flag:
            self.add_log("BUILD_TREE_COMPLETE", f"Árvore construída com {node_count} nós")
    
    def search_tree_routine(self, duration_seconds, log_interval_sec):
        """Rotina 2: Pesquisa valores na árvore mantendo a memória alocada"""
        self.add_log("SEARCH_TREE_START", f"Iniciando pesquisas por {duration_seconds} segundos")
        
        start_time = time.time()
        last_log_time = start_time
        search_count = 0
        
        while not self.stop_flag:
            elapsed = time.time() - start_time
            
            # Verifica se terminou a duração
            if elapsed >= duration_seconds:
                self.add_log("SEARCH_TREE_TIMEOUT", f"Duração de {duration_seconds}s atingida")
                break
            
            # Realiza pesquisas aleatórias
            if self.root:
                for _ in range(100):  # Busca em lotes
                    if self.stop_flag:
                        break
                    value = random.randint(1, 1000000)
                    self.root.search(value)
                    search_count += 1
            
            # Log periódico
            if time.time() - last_log_time >= log_interval_sec:
                node_count = self.root.count_nodes() if self.root else 0
                self.add_log("SEARCH_TREE_PROGRESS", 
                           f"Pesquisas: {search_count}, Nós: {node_count}")
                last_log_time = time.time()
            
            time.sleep(0.05)
        
        self.add_log("SEARCH_TREE_COMPLETE", f"Total de pesquisas: {search_count}")
    
    def run_stress_test(self, memory_mb, duration_seconds, log_interval_sec):
        """Executa o teste de stress completo"""
        if self.is_running:
            return False, "Teste já está em execução"
        
        with self.lock:
            self.is_running = True
            self.stop_flag = False
            self.logs = []
            self.root = None
            self.config = {
                'memory_mb': memory_mb,
                'duration_seconds': duration_seconds,
                'log_interval_sec': log_interval_sec
            }
        
        self.add_log("STRESS_TEST_START", 
                    f"Configuração: {memory_mb}MB, {duration_seconds}s, log a cada {log_interval_sec}s")
        
        # Calcula o tamanho do payload por nó para atingir a memória alvo
        # Estimativa: cada nó ocupa aproximadamente payload_size + overhead
        payload_size_kb = 100  # Ajuste conforme necessário
        
        try:
            # Fase 1: Construir a árvore
            self.build_tree_routine(memory_mb, payload_size_kb)
            
            # Fase 2: Pesquisar na árvore
            if not self.stop_flag:
                self.search_tree_routine(duration_seconds, log_interval_sec)
            
            self.add_log("STRESS_TEST_COMPLETE", "Teste de stress finalizado com sucesso")
            
        except Exception as e:
            self.add_log("STRESS_TEST_ERROR", f"Erro durante o teste: {str(e)}")
        
        finally:
            with self.lock:
                self.is_running = False
                # Mantém a árvore na memória até que seja explicitamente limpa
        
        return True, "Teste concluído"
    
    def stop_test(self):
        """Para o teste em execução"""
        self.stop_flag = True
        self.add_log("STRESS_TEST_STOPPED", "Teste interrompido pelo usuário")
    
    def clear_memory(self):
        """Limpa a árvore e libera memória"""
        with self.lock:
            self.root = None
            self.add_log("MEMORY_CLEARED", "Árvore removida, memória liberada")


# Instância global do gerenciador
stress_manager = StressTestManager()


# Rotas HTTP
@app.route('/')
def index():
    """Página inicial com informações da API"""
    return jsonify({
        'service': 'Kubernetes Memory Stress Test',
        'version': '1.0',
        'endpoints': {
            '/start': 'POST - Inicia o teste de stress',
            '/stop': 'POST - Para o teste em execução',
            '/status': 'GET - Status atual do teste',
            '/logs': 'GET - Retorna os logs do teste',
            '/clear': 'POST - Limpa a memória alocada',
            '/health': 'GET - Health check'
        }
    })


@app.route('/start', methods=['POST'])
def start_stress():
    """Inicia o teste de stress"""
    data = request.get_json() or {}
    
    memory_mb = data.get('memory_mb', None)
    memory_percent = data.get('memory_percent', None)
    duration_seconds = data.get('duration_seconds', 60)
    log_interval_sec = data.get('log_interval_sec', 5)
    
    # Calcula memória alvo baseado no percentual, se fornecido
    if memory_percent is not None:
        if memory_percent < 1 or memory_percent > 95:
            return jsonify({'error': 'memory_percent deve estar entre 1 e 95'}), 400
        
        # Obtém memória total do sistema
        total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        memory_mb = int(total_memory_mb * memory_percent / 100)
        
    elif memory_mb is None:
        return jsonify({'error': 'Forneça memory_mb ou memory_percent'}), 400
    
    # Validações
    if memory_mb < 10 or memory_mb > 10000:
        return jsonify({'error': 'memory_mb deve estar entre 10 e 10000'}), 400
    
    if duration_seconds < 5 or duration_seconds > 3600:
        return jsonify({'error': 'duration_seconds deve estar entre 5 e 3600'}), 400
    
    if log_interval_sec < 1 or log_interval_sec > 60:
        return jsonify({'error': 'log_interval_sec deve estar entre 1 e 60'}), 400
    
    # Inicia o teste em uma thread separada
    def run_test():
        stress_manager.run_stress_test(memory_mb, duration_seconds, log_interval_sec)
    
    thread = threading.Thread(target=run_test, daemon=True)
    thread.start()
    
    return jsonify({
        'status': 'started',
        'config': {
            'memory_mb': memory_mb,
            'memory_percent': memory_percent if memory_percent else None,
            'total_system_memory_mb': round(psutil.virtual_memory().total / (1024 * 1024), 2),
            'duration_seconds': duration_seconds,
            'log_interval_sec': log_interval_sec
        }
    })


@app.route('/stop', methods=['POST'])
def stop_stress():
    """Para o teste de stress"""
    if not stress_manager.is_running:
        return jsonify({'error': 'Nenhum teste em execução'}), 400
    
    stress_manager.stop_test()
    return jsonify({'status': 'stopping'})


@app.route('/status', methods=['GET'])
def get_status():
    """Retorna o status atual"""
    total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
    current_memory_mb = stress_manager.get_memory_usage_mb()
    memory_percent = (current_memory_mb / total_memory_mb) * 100
    
    return jsonify({
        'is_running': stress_manager.is_running,
        'current_memory_mb': round(current_memory_mb, 2),
        'current_memory_percent': round(memory_percent, 2),
        'total_system_memory_mb': round(total_memory_mb, 2),
        'config': stress_manager.config,
        'total_logs': len(stress_manager.logs)
    })


@app.route('/logs', methods=['GET'])
def get_logs():
    """Retorna os logs do teste"""
    limit = request.args.get('limit', type=int, default=None)
    
    with stress_manager.lock:
        logs = stress_manager.logs.copy()
    
    if limit:
        logs = logs[-limit:]
    
    return jsonify({
        'total': len(stress_manager.logs),
        'logs': logs
    })


@app.route('/clear', methods=['POST'])
def clear_memory():
    """Limpa a memória alocada"""
    if stress_manager.is_running:
        return jsonify({'error': 'Pare o teste antes de limpar a memória'}), 400
    
    stress_manager.clear_memory()
    return jsonify({'status': 'memory_cleared'})


@app.route('/health', methods=['GET'])
def health():
    """Health check para Kubernetes"""
    return jsonify({
        'status': 'healthy',
        'memory_mb': round(stress_manager.get_memory_usage_mb(), 2)
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Kubernetes Memory Stress Test - Árvore Binária")
    print("=" * 60)
    print("Endpoints disponíveis:")
    print("  POST /start - Inicia teste de stress")
    print("  POST /stop - Para o teste")
    print("  GET /status - Status atual")
    print("  GET /logs - Visualizar logs")
    print("  POST /clear - Limpar memória")
    print("  GET /health - Health check")
    print("=" * 60)
    
    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=8080, debug=False)