#!/usr/bin/env python3
"""
PostgreSQL Stress Test Application
Executa testes de carga no PostgreSQL sem Docker
"""

import psycopg2
import threading
import time
import random
import configparser
import logging
import os
import sys
from datetime import datetime
import signal
import statistics

class PostgreSQLStressTest:
    def __init__(self, config_file='config/database.conf'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Configurações do banco
        self.db_config = {
            'host': self.config.get('database', 'host'),
            'port': self.config.getint('database', 'port'),
            'database': self.config.get('database', 'database'),
            'user': self.config.get('database', 'username'),
            'password': self.config.get('database', 'password')
        }
        
        # Configurações do teste
        self.concurrent_connections = self.config.getint('stress_test', 'concurrent_connections')
        self.test_duration = self.config.getint('stress_test', 'test_duration')
        self.query_interval = self.config.getfloat('stress_test', 'query_interval')
        self.test_table = self.config.get('stress_test', 'test_table')
        self.records_to_insert = self.config.getint('stress_test', 'records_to_insert')
        
        # Operações habilitadas
        self.enable_select = self.config.getboolean('stress_test', 'enable_select')
        self.enable_insert = self.config.getboolean('stress_test', 'enable_insert')
        self.enable_update = self.config.getboolean('stress_test', 'enable_update')
        self.enable_delete = self.config.getboolean('stress_test', 'enable_delete')
        
        # Controle de execução
        self.running = True
        self.threads = []
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'response_times': [],
            'start_time': None,
            'end_time': None
        }
        self.stats_lock = threading.Lock()
        
        # Configurar logging
        self.setup_logging()
        
        # Configurar handler para interrupção
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def setup_logging(self):
        """Configura o sistema de logging"""
        log_level = self.config.get('logging', 'log_level', fallback='INFO')
        log_file = self.config.get('logging', 'log_file', fallback='logs/stress_test.log')
        console_output = self.config.getboolean('logging', 'enable_console_output', fallback=True)
        
        # Criar diretório de logs se não existir
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout) if console_output else logging.NullHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)

    def signal_handler(self, signum, frame):
        """Handler para interrupção do programa"""
        self.logger.info(f"Recebido sinal {signum}. Finalizando teste...")
        self.running = False

    def test_connection(self):
        """Testa a conexão com o banco de dados"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            self.logger.info(f"Conexão bem-sucedida: {version[0]}")
            return True
        except Exception as e:
            self.logger.error(f"Erro na conexão: {e}")
            return False

    def create_test_table(self):
        """Cria a tabela de teste"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Criar tabela se não existir
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.test_table} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    age INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    random_data TEXT
                )
            """)
            
            # Inserir dados iniciais
            self.logger.info(f"Inserindo {self.records_to_insert} registros iniciais...")
            for i in range(self.records_to_insert):
                cursor.execute(f"""
                    INSERT INTO {self.test_table} (name, email, age, random_data)
                    VALUES (%s, %s, %s, %s)
                """, (
                    f"User_{i}",
                    f"user_{i}@example.com",
                    random.randint(18, 80),
                    f"Random data {random.randint(1000, 9999)}"
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            self.logger.info("Tabela de teste criada com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao criar tabela: {e}")
            return False

    def execute_query(self, query, params=None):
        """Executa uma query e mede o tempo de resposta"""
        start_time = time.time()
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # Se for SELECT, buscar resultados
            if query.strip().upper().startswith('SELECT'):
                cursor.fetchall()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            response_time = time.time() - start_time
            
            with self.stats_lock:
                self.stats['successful_queries'] += 1
                self.stats['response_times'].append(response_time)
            
            return True, response_time
        except Exception as e:
            response_time = time.time() - start_time
            with self.stats_lock:
                self.stats['failed_queries'] += 1
            self.logger.error(f"Erro na query: {e}")
            return False, response_time

    def worker_thread(self, thread_id):
        """Thread worker que executa queries"""
        self.logger.info(f"Thread {thread_id} iniciada")
        
        while self.running:
            try:
                # Escolher operação aleatória
                operations = []
                if self.enable_select:
                    operations.append('select')
                if self.enable_insert:
                    operations.append('insert')
                if self.enable_update:
                    operations.append('update')
                if self.enable_delete:
                    operations.append('delete')
                
                if not operations:
                    self.logger.warning("Nenhuma operação habilitada!")
                    break
                
                operation = random.choice(operations)
                
                # Executar operação
                if operation == 'select':
                    query = f"SELECT * FROM {self.test_table} ORDER BY RANDOM() LIMIT 10"
                    self.execute_query(query)
                
                elif operation == 'insert':
                    query = f"""
                        INSERT INTO {self.test_table} (name, email, age, random_data)
                        VALUES (%s, %s, %s, %s)
                    """
                    params = (
                        f"StressUser_{random.randint(1, 10000)}",
                        f"stress_{random.randint(1, 10000)}@test.com",
                        random.randint(18, 80),
                        f"Stress test data {random.randint(1000, 9999)}"
                    )
                    self.execute_query(query, params)
                
                elif operation == 'update':
                    query = f"""
                        UPDATE {self.test_table} 
                        SET age = %s, random_data = %s 
                        WHERE id = (SELECT id FROM {self.test_table} ORDER BY RANDOM() LIMIT 1)
                    """
                    params = (
                        random.randint(18, 80),
                        f"Updated data {random.randint(1000, 9999)}"
                    )
                    self.execute_query(query, params)
                
                elif operation == 'delete':
                    # Deletar apenas registros criados pelo stress test
                    query = f"""
                        DELETE FROM {self.test_table} 
                        WHERE name LIKE 'StressUser_%' 
                        AND id = (SELECT id FROM {self.test_table} WHERE name LIKE 'StressUser_%' ORDER BY RANDOM() LIMIT 1)
                    """
                    self.execute_query(query)
                
                with self.stats_lock:
                    self.stats['total_queries'] += 1
                
                # Aguardar intervalo
                time.sleep(self.query_interval)
                
            except Exception as e:
                self.logger.error(f"Erro na thread {thread_id}: {e}")
        
        self.logger.info(f"Thread {thread_id} finalizada")

    def run_stress_test(self):
        """Executa o teste de stress"""
        self.logger.info("=== INICIANDO TESTE DE STRESS ===")
        self.logger.info(f"Conexões simultâneas: {self.concurrent_connections}")
        self.logger.info(f"Duração: {self.test_duration} segundos")
        self.logger.info(f"Intervalo entre queries: {self.query_interval}s")
        
        # Testar conexão
        if not self.test_connection():
            self.logger.error("Falha na conexão. Abortando teste.")
            return False
        
        # Criar tabela de teste
        if not self.create_test_table():
            self.logger.error("Falha ao criar tabela. Abortando teste.")
            return False
        
        # Iniciar estatísticas
        self.stats['start_time'] = time.time()
        
        # Criar e iniciar threads
        for i in range(self.concurrent_connections):
            thread = threading.Thread(target=self.worker_thread, args=(i,))
            thread.start()
            self.threads.append(thread)
        
        # Aguardar duração do teste
        try:
            time.sleep(self.test_duration)
        except KeyboardInterrupt:
            self.logger.info("Teste interrompido pelo usuário")
        
        # Parar execução
        self.running = False
        self.stats['end_time'] = time.time()
        
        # Aguardar threads terminarem
        for thread in self.threads:
            thread.join()
        
        # Exibir estatísticas
        self.show_statistics()
        
        return True

    def show_statistics(self):
        """Exibe estatísticas do teste"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*50)
        print("ESTATÍSTICAS DO TESTE DE STRESS")
        print("="*50)
        print(f"Duração total: {duration:.2f} segundos")
        print(f"Total de queries: {self.stats['total_queries']}")
        print(f"Queries bem-sucedidas: {self.stats['successful_queries']}")
        print(f"Queries com falha: {self.stats['failed_queries']}")
        print(f"Taxa de sucesso: {(self.stats['successful_queries']/self.stats['total_queries']*100):.2f}%")
        print(f"Queries por segundo: {self.stats['total_queries']/duration:.2f}")
        
        if self.stats['response_times']:
            print(f"Tempo médio de resposta: {statistics.mean(self.stats['response_times']):.4f}s")
            print(f"Tempo mínimo: {min(self.stats['response_times']):.4f}s")
            print(f"Tempo máximo: {max(self.stats['response_times']):.4f}s")
            print(f"Mediana: {statistics.median(self.stats['response_times']):.4f}s")
        
        print("="*50)

def main():
    """Função principal"""
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = 'config/database.conf'
    
    if not os.path.exists(config_file):
        print(f"Arquivo de configuração não encontrado: {config_file}")
        sys.exit(1)
    
    stress_test = PostgreSQLStressTest(config_file)
    stress_test.run_stress_test()

if __name__ == "__main__":
    main()