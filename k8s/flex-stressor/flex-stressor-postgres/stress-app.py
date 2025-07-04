# stress_app.py
import asyncio
import asyncpg
import psutil
import threading
import time
import random
import json
import os
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StressConfig:
    def __init__(self):
        self.cpu_cores = int(os.getenv('CPU_CORES', mp.cpu_count()))
        self.memory_mb = int(os.getenv('MEMORY_MB', 100))
        self.duration_sec = int(os.getenv('DURATION_SEC', 300))
        self.db_connections = int(os.getenv('DB_CONNECTIONS', 10))
        self.db_host = os.getenv('DB_HOST', 'postgres-service')
        self.db_port = int(os.getenv('DB_PORT', 5432))
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', 'password')
        self.db_name = os.getenv('DB_NAME', 'stressdb')

class DatabaseStresser:
    def __init__(self, config: StressConfig):
        self.config = config
        self.db_pool = None
        self.stop_event = threading.Event()
        
    async def init_database(self):
        """Inicializa o pool de conexões e cria as tabelas"""
        try:
            # Criar pool de conexões
            self.db_pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                user=self.config.db_user,
                password=self.config.db_password,
                database=self.config.db_name,
                min_size=5,
                max_size=self.config.db_connections
            )
            
            # Criar tabelas
            await self.create_tables()
            logger.info("✅ Banco de dados inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco: {e}")
            raise
    
    async def create_tables(self):
        """Cria as tabelas necessárias para o teste"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS stress_data (
                id SERIAL PRIMARY KEY,
                data TEXT NOT NULL,
                number_value INTEGER,
                float_value FLOAT,
                timestamp_value TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                json_data JSONB
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS stress_logs (
                id SERIAL PRIMARY KEY,
                level VARCHAR(10),
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS stress_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(50),
                metric_value FLOAT,
                tags JSONB,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_stress_data_number ON stress_data(number_value)",
            "CREATE INDEX IF NOT EXISTS idx_stress_data_timestamp ON stress_data(timestamp_value)",
            "CREATE INDEX IF NOT EXISTS idx_stress_logs_level ON stress_logs(level)",
            "CREATE INDEX IF NOT EXISTS idx_stress_metrics_name ON stress_metrics(metric_name)"
        ]
        
        async with self.db_pool.acquire() as conn:
            for query in queries:
                await conn.execute(query)
    
    def cpu_stress(self, duration: int):
        """Executa stress de CPU"""
        logger.info(f"🔥 Iniciando stress de CPU com {self.config.cpu_cores} cores por {duration}s")
        
        def cpu_worker(core_id: int):
            end_time = time.time() + duration
            counter = 0
            
            while time.time() < end_time and not self.stop_event.is_set():
                # Operações matemáticas intensivas
                for _ in range(100000):
                    counter += random.randint(1, 1000) ** 2
                
                # Pequena pausa para não sobrecarregar demais
                if counter % 10000000 == 0:
                    time.sleep(0.001)
            
            logger.info(f"✅ CPU Core {core_id} finalizou stress")
        
        # Criar threads para cada core
        threads = []
        for i in range(self.config.cpu_cores):
            thread = threading.Thread(target=cpu_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Aguardar todas as threads terminarem
        for thread in threads:
            thread.join()
    
    def memory_stress(self, duration: int):
        """Executa stress de memória"""
        logger.info(f"🧠 Iniciando stress de memória: {self.config.memory_mb}MB por {duration}s")
        
        data_chunks = []
        end_time = time.time() + duration
        allocated_mb = 0
        
        while time.time() < end_time and allocated_mb < self.config.memory_mb and not self.stop_event.is_set():
            # Aloca 1MB por vez
            chunk = bytearray(1024 * 1024)  # 1MB
            
            # Preenche com dados aleatórios
            for i in range(0, len(chunk), 1024):
                chunk[i:i+1024] = bytes([random.randint(0, 255) for _ in range(min(1024, len(chunk)-i))])
            
            data_chunks.append(chunk)
            allocated_mb += 1
            
            if allocated_mb % 50 == 0:
                logger.info(f"📊 Memória alocada: {allocated_mb}MB")
            
            time.sleep(0.1)
        
        logger.info(f"✅ Stress de memória concluído: {allocated_mb}MB alocados")
        
        # Mantém os dados na memória até o fim da duração
        while time.time() < end_time and not self.stop_event.is_set():
            time.sleep(1)
    
    async def database_stress(self, duration: int):
        """Executa stress no banco de dados"""
        logger.info(f"🗄️ Iniciando stress de banco com {self.config.db_connections} conexões por {duration}s")
        
        # Criar tasks para workers assíncronos
        tasks = []
        for worker_id in range(self.config.db_connections):
            task = asyncio.create_task(self.database_worker(worker_id, duration))
            tasks.append(task)
        
        # Aguardar todos os workers terminarem
        await asyncio.gather(*tasks)
        logger.info("✅ Stress de banco de dados concluído")
    
    async def database_worker(self, worker_id: int, duration: int):
        """Worker individual para operações no banco"""
        end_time = time.time() + duration
        operations = 0
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                operation = random.randint(0, 5)
                
                if operation == 0:
                    await self.insert_stress_data(worker_id)
                elif operation == 1:
                    await self.select_stress_data()
                elif operation == 2:
                    await self.update_stress_data()
                elif operation == 3:
                    await self.delete_stress_data()
                elif operation == 4:
                    await self.complex_query()
                else:
                    await self.insert_metrics(worker_id)
                
                operations += 1
                
                # Pequena pausa
                await asyncio.sleep(random.uniform(0.01, 0.1))
                
            except Exception as e:
                logger.error(f"Erro no worker {worker_id}: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"🔧 Worker {worker_id} executou {operations} operações")
    
    async def insert_stress_data(self, worker_id: int):
        """Insere dados de teste"""
        data = f"Worker {worker_id} - Data {random.randint(1, 10000)} - {datetime.now().isoformat()}"
        json_data = json.dumps({
            "worker_id": worker_id,
            "random": random.randint(1, 1000),
            "timestamp": datetime.now().isoformat()
        })
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO stress_data (data, number_value, float_value, json_data) 
                VALUES ($1, $2, $3, $4)
                """,
                data, 
                random.randint(1, 100000), 
                random.uniform(0, 1000), 
                json_data
            )
    
    async def select_stress_data(self):
        """Executa consultas de seleção"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, data, number_value, float_value 
                FROM stress_data 
                WHERE number_value > $1 
                ORDER BY timestamp_value DESC 
                LIMIT 100
                """,
                random.randint(1, 50000)
            )
            return len(rows)
    
    async def update_stress_data(self):
        """Executa atualizações"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE stress_data 
                SET float_value = $1, data = $2 
                WHERE number_value BETWEEN $3 AND $4
                """,
                random.uniform(0, 2000),
                f"Updated at {datetime.now().isoformat()}",
                random.randint(1, 10000),
                random.randint(10000, 20000)
            )
    
    async def delete_stress_data(self):
        """Executa deleções"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM stress_data 
                WHERE id IN (
                    SELECT id FROM stress_data 
                    WHERE timestamp_value < NOW() - INTERVAL '1 minute' 
                    LIMIT 10
                )
                """
            )
    
    async def complex_query(self):
        """Executa consulta complexa"""
        async with self.db_pool.acquire() as conn:
            await conn.fetch(
                """
                SELECT 
                    COUNT(*) as total_records,
                    AVG(number_value) as avg_number,
                    MAX(float_value) as max_float,
                    MIN(timestamp_value) as min_timestamp,
                    COUNT(DISTINCT EXTRACT(HOUR FROM timestamp_value)) as distinct_hours
                FROM stress_data 
                WHERE timestamp_value >= NOW() - INTERVAL '5 minutes'
                GROUP BY EXTRACT(HOUR FROM timestamp_value)
                ORDER BY total_records DESC
                """
            )
    
    async def insert_metrics(self, worker_id: int):
        """Insere métricas de monitoramento"""
        metrics = ["cpu_usage", "memory_usage", "disk_io", "network_io", "db_connections"]
        metric = random.choice(metrics)
        value = random.uniform(0, 100)
        tags = json.dumps({"worker_id": worker_id, "type": "stress_test"})
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO stress_metrics (metric_name, metric_value, tags) 
                VALUES ($1, $2, $3)
                """,
                metric, value, tags
            )
    
    async def insert_logs(self):
        """Insere logs periodicamente"""
        levels = ["INFO", "WARN", "ERROR", "DEBUG"]
        messages = [
            "Sistema funcionando normalmente",
            "Alta utilização de CPU detectada",
            "Erro de conexão temporário",
            "Processo de limpeza executado",
            "Backup realizado com sucesso"
        ]
        
        while not self.stop_event.is_set():
            try:
                level = random.choice(levels)
                message = random.choice(messages)
                
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO stress_logs (level, message) VALUES ($1, $2)",
                        level, message
                    )
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Erro ao inserir log: {e}")
                await asyncio.sleep(1)
    
    async def cleanup_old_data(self):
        """Limpa dados antigos periodicamente"""
        while not self.stop_event.is_set():
            try:
                queries = [
                    "DELETE FROM stress_data WHERE timestamp_value < NOW() - INTERVAL '10 minutes'",
                    "DELETE FROM stress_logs WHERE created_at < NOW() - INTERVAL '10 minutes'",
                    "DELETE FROM stress_metrics WHERE recorded_at < NOW() - INTERVAL '10 minutes'"
                ]
                
                async with self.db_pool.acquire() as conn:
                    for query in queries:
                        result = await conn.execute(query)
                        logger.info(f"🧹 Limpeza executada: {result}")
                
                await asyncio.sleep(60)  # Limpa a cada minuto
                
            except Exception as e:
                logger.error(f"Erro na limpeza: {e}")
                await asyncio.sleep(10)
    
    async def get_system_metrics(self):
        """Coleta métricas do sistema"""
        while not self.stop_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                logger.info(f"📊 CPU: {cpu_percent}% | RAM: {memory.percent}% | Disk: {disk.percent}%")
                
                # Inserir métricas no banco
                metrics_data = [
                    ("system_cpu", cpu_percent),
                    ("system_memory", memory.percent),
                    ("system_disk", disk.percent)
                ]
                
                async with self.db_pool.acquire() as conn:
                    for metric_name, value in metrics_data:
                        await conn.execute(
                            "INSERT INTO stress_metrics (metric_name, metric_value, tags) VALUES ($1, $2, $3)",
                            metric_name, value, json.dumps({"source": "system"})
                        )
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Erro ao coletar métricas: {e}")
                await asyncio.sleep(5)
    
    async def close(self):
        """Fecha o pool de conexões"""
        if self.db_pool:
            await self.db_pool.close()

async def main():
    logger.info("🚀 Iniciando Stress Test Completo com PostgreSQL")
    
    config = StressConfig()
    stresser = DatabaseStresser(config)
    
    try:
        # Inicializar banco
        await stresser.init_database()
        
        logger.info("⚙️ Configuração:")
        logger.info(f"   - CPU Cores: {config.cpu_cores}")
        logger.info(f"   - Memória: {config.memory_mb}MB")
        logger.info(f"   - Duração: {config.duration_sec}s")
        logger.info(f"   - Conexões DB: {config.db_connections}")
        logger.info(f"   - Banco: {config.db_host}:{config.db_port}")
        
        # Limpeza inicial
        await stresser.cleanup_old_data()
        
        # Criar tasks para execução paralela
        tasks = []
        
        # Task para stress de banco
        tasks.append(asyncio.create_task(stresser.database_stress(config.duration_sec)))
        
        # Task para inserir logs
        tasks.append(asyncio.create_task(stresser.insert_logs()))
        
        # Task para limpeza periódica
        tasks.append(asyncio.create_task(stresser.cleanup_old_data()))
        
        # Task para métricas do sistema
        tasks.append(asyncio.create_task(stresser.get_system_metrics()))
        
        # Executar stress de CPU e memória em threads separadas
        cpu_thread = threading.Thread(target=stresser.cpu_stress, args=(config.duration_sec,))
        memory_thread = threading.Thread(target=stresser.memory_stress, args=(config.duration_sec,))
        
        cpu_thread.start()
        memory_thread.start()
        
        # Aguardar duração do teste
        await asyncio.sleep(config.duration_sec)
        
        # Parar todas as tasks
        stresser.stop_event.set()
        
        # Cancelar tasks assíncronas
        for task in tasks:
            task.cancel()
        
        # Aguardar threads terminarem
        cpu_thread.join(timeout=10)
        memory_thread.join(timeout=10)
        
        logger.info("🎉 Stress Test Completo Finalizado!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante execução: {e}")
        raise
    finally:
        await stresser.close()

if __name__ == "__main__":
    asyncio.run(main())