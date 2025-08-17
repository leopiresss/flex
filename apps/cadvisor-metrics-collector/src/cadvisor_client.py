import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yaml

class CAdvisorClient:
    """Cliente para conectar e coletar métricas do cAdvisor"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.base_url = f"{self.config['cadvisor']['protocol']}://{self.config['cadvisor']['host']}:{self.config['cadvisor']['port']}"
        self.session = requests.Session()
        self.logger = self._setup_logger()
        self.debug_mode = self.config.get('debug', False)
        
    def _load_config(self, config_path: str) -> Dict:
        """Carrega configurações do arquivo YAML"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config
        except FileNotFoundError:
            self.logger.warning(f"Arquivo de configuração {config_path} não encontrado. Usando configuração padrão.")
            return {
                'cadvisor': {'host': 'localhost', 'port': 8080, 'protocol': 'http', 'timeout': 30},
                'collection': {'interval_seconds': 60, 'duration_minutes': 60},
                'debug': True  # Habilitar debug por padrão quando config não existe
            }
    
    def _setup_logger(self) -> logging.Logger:
        """Configura logging"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            logger.setLevel(logging.DEBUG)  # Mudado para DEBUG
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def test_connection(self) -> bool:
        """Testa conexão com cAdvisor"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1.3/machine",
                timeout=self.config['cadvisor']['timeout']
            )
            response.raise_for_status()
            self.logger.info("Conexão com cAdvisor estabelecida com sucesso")
            
            # Debug: mostrar estrutura da resposta
            if self.debug_mode:
                machine_data = response.json()
                self.logger.debug(f"Estrutura da resposta /machine: {list(machine_data.keys())}")
            
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao conectar com cAdvisor: {e}")
            return False
    
    def debug_api_structure(self):
        """Método para debugar a estrutura da API do cAdvisor"""
        self.logger.info("=== DEBUG: Analisando estrutura da API ===")
        
        try:
            # Testar endpoint de containers
            response = self.session.get(f"{self.base_url}/api/v1.3/containers")
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Containers endpoint OK. Tipo de resposta: {type(data)}")
                
                if isinstance(data, dict):
                    self.logger.info(f"Número de containers: {len(data)}")
                    
                    # Analisar primeiro container
                    for i, (path, info) in enumerate(data.items()):
                        if i >= 3:  # Limitar a 3 containers para debug
                            break
                            
                        self.logger.info(f"\n--- Container {i+1}: {path} ---")
                        self.logger.info(f"Tipo de info: {type(info)}")
                        
                        if isinstance(info, dict):
                            self.logger.info(f"Chaves disponíveis: {list(info.keys())}")
                            
                            # Analisar stats
                            stats = info.get('stats', [])
                            self.logger.info(f"Stats - Tipo: {type(stats)}, Tamanho: {len(stats) if isinstance(stats, list) else 'N/A'}")
                            
                            if isinstance(stats, list) and stats:
                                latest_stat = stats[-1]
                                self.logger.info(f"Último stat - Tipo: {type(latest_stat)}")
                                if isinstance(latest_stat, dict):
                                    self.logger.info(f"Chaves do stat: {list(latest_stat.keys())}")
                                    
                                    # Verificar timestamp
                                    timestamp = latest_stat.get('timestamp')
                                    self.logger.info(f"Timestamp: {timestamp} (tipo: {type(timestamp)})")
                            
                            # Analisar spec
                            spec = info.get('spec', {})
                            if isinstance(spec, dict):
                                self.logger.info(f"Spec disponível com chaves: {list(spec.keys())}")
                        else:
                            self.logger.warning(f"Info do container não é dict: {type(info)}")
                
            else:
                self.logger.error(f"Erro no endpoint containers: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Erro durante debug: {e}")
    
    def get_machine_info(self) -> Dict:
        """Obtém informações da máquina"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1.3/machine",
                timeout=self.config['cadvisor']['timeout']
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao obter informações da máquina: {e}")
            return {}
    
    def get_containers_info(self, count: int = 1) -> Dict:
        """Obtém informações de todos os containers com histórico limitado"""
        try:
            params = {'count': count} if count > 0 else {}
            response = self.session.get(
                f"{self.base_url}/api/v1.3/containers",
                params=params,
                timeout=self.config['cadvisor']['timeout']
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Debug da resposta
            if self.debug_mode:
                self.logger.debug(f"Resposta da API - Tipo: {type(data)}, Tamanho: {len(data) if isinstance(data, dict) else 'N/A'}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao obter informações dos containers: {e}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON da resposta: {e}")
            return {}
    
    def collect_metrics_continuously(self, duration_minutes: int = None) -> List[Dict]:
        """Coleta métricas continuamente por um período especificado"""
        if duration_minutes is None:
            duration_minutes = self.config['collection']['duration_minutes']
        
        interval = self.config['collection']['interval_seconds']
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        metrics_data = []
        
        self.logger.info(f"Iniciando coleta de métricas por {duration_minutes} minutos (intervalo: {interval}s)")
        
        # Executar debug inicial se habilitado
        if self.debug_mode:
            self.debug_api_structure()
        
        collection_count = 0
        while datetime.now() < end_time:
            collection_count += 1
            self.logger.info(f"Coleta #{collection_count} - {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                # Coleta métricas de todos os containers
                containers_data = self.get_containers_info(count=1)
                
                if not containers_data:
                    self.logger.warning("Nenhum dado de container retornado pela API")
                    time.sleep(interval)
                    continue
                
                # Verificar se é um dicionário válido
                if not isinstance(containers_data, dict):
                    self.logger.error(f"Resposta da API não é um dicionário: {type(containers_data)}")
                    time.sleep(interval)
                    continue
                
                containers_processed = 0
                containers_with_stats = 0
                containers_with_errors = 0
                
                # Processar cada container
                for container_path, container_info in containers_data.items():
                    containers_processed += 1
                    
                    try:
                        # Debug detalhado para primeiro container em primeira coleta
                        if collection_count == 1 and containers_processed == 1 and self.debug_mode:
                            self.logger.debug(f"DEBUG Container: {container_path}")
                            self.logger.debug(f"DEBUG Info type: {type(container_info)}")
                            if isinstance(container_info, dict):
                                self.logger.debug(f"DEBUG Info keys: {list(container_info.keys())}")
                        
                        # Validar se container tem informações básicas
                        if not isinstance(container_info, dict):
                            self.logger.warning(f"Container {container_path}: dados não são dict - tipo: {type(container_info)}")
                            containers_with_errors += 1
                            continue
                        
                        # Verificar se há stats disponíveis
                        stats_list = container_info.get('stats', [])
                        if not stats_list:
                            self.logger.debug(f"Container {container_path}: campo 'stats' vazio ou ausente")
                            continue
                            
                        if not isinstance(stats_list, list):
                            self.logger.warning(f"Container {container_path}: 'stats' não é uma lista - tipo: {type(stats_list)}")
                            containers_with_errors += 1
                            continue
                        
                        # Pegar o stat mais recente
                        latest_stat = stats_list[-1]
                        if not isinstance(latest_stat, dict):
                            self.logger.warning(f"Container {container_path}: último stat não é dict - tipo: {type(latest_stat)}")
                            containers_with_errors += 1
                            continue
                        
                        # Validar timestamp do stat
                        stat_timestamp = latest_stat.get('timestamp')
                        if not stat_timestamp:
                            self.logger.warning(f"Container {container_path}: timestamp ausente no stat")
                            containers_with_errors += 1
                            continue
                        
                        containers_with_stats += 1
                        
                        # Extrair nome do container
                        container_name = self._extract_container_name(container_path, container_info)
                        
                        metric_entry = {
                            'collection_timestamp': datetime.now().isoformat(),
                            'stat_timestamp': stat_timestamp,
                            'container_path': container_path,
                            'container_name': container_name,
                            'cpu_usage': self._extract_cpu_usage(latest_stat),
                            'memory_usage': self._extract_memory_usage(latest_stat),
                            'network_stats': self._extract_network_stats(latest_stat),
                            'filesystem_stats': self._extract_filesystem_stats(latest_stat)
                        }
                        
                        metrics_data.append(metric_entry)
                        
                        # Debug para primeiro container válido
                        if containers_with_stats == 1 and collection_count == 1 and self.debug_mode:
                            self.logger.debug(f"DEBUG Primeiro metric_entry criado com sucesso para: {container_name}")
                        
                    except Exception as e:
                        self.logger.error(f"Erro ao processar container {container_path}: {e}")
                        containers_with_errors += 1
                        continue
                
                self.logger.info(f"Processados: {containers_processed} containers, "
                               f"Com stats válidos: {containers_with_stats}, "
                               f"Com erros: {containers_with_errors}")
                
            except Exception as e:
                self.logger.error(f"Erro durante coleta #{collection_count}: {e}")
            
            # Aguardar próximo intervalo
            if datetime.now() < end_time:
                time.sleep(interval)
        
        self.logger.info(f"Coleta finalizada. Total de {len(metrics_data)} registros coletados")
        return metrics_data
    
    def _extract_container_name(self, container_path: str, container_info: Dict) -> str:
        """Extrai nome limpo do container"""
        try:
            # Tentar obter nome do spec primeiro
            spec = container_info.get('spec', {})
            if isinstance(spec, dict) and 'labels' in spec:
                labels = spec['labels']
                if isinstance(labels, dict):
                    # Kubernetes labels comuns
                    for label_key in ['io.kubernetes.pod.name', 'io.kubernetes.container.name', 'name']:
                        if label_key in labels and labels[label_key]:
                            return str(labels[label_key])
            
            # Fallback para nome do container_info
            name = container_info.get('name', '')
            if name and name != 'unknown':
                return str(name)
            
            # Último fallback: limpar o path
            if container_path and container_path != '/':
                # Remove barras e pega último segmento
                clean_name = container_path.strip('/').split('/')[-1]
                return clean_name if clean_name else 'root'
            
            return 'system'
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair nome do container {container_path}: {e}")
            return 'unknown'
    
    def _extract_cpu_usage(self, stats: Dict) -> Dict:
        """Extrai métricas de CPU com validação"""
        try:
            cpu_stats = stats.get('cpu', {})
            if not isinstance(cpu_stats, dict):
                return {'total_usage': 0, 'usage_per_cpu': [], 'system_usage': 0, 'user_usage': 0, 'load_average': 0}
            
            usage = cpu_stats.get('usage', {})
            if not isinstance(usage, dict):
                usage = {}
            
            return {
                'total_usage': usage.get('total', 0),
                'usage_per_cpu': usage.get('per_cpu_usage', []) if isinstance(usage.get('per_cpu_usage'), list) else [],
                'system_usage': usage.get('system', 0),
                'user_usage': usage.get('user', 0),
                'load_average': cpu_stats.get('load_average', 0)
            }
        except Exception as e:
            self.logger.warning(f"Erro ao extrair CPU stats: {e}")
            return {'total_usage': 0, 'usage_per_cpu': [], 'system_usage': 0, 'user_usage': 0, 'load_average': 0}
    
    def _extract_memory_usage(self, stats: Dict) -> Dict:
        """Extrai métricas de memória com validação"""
        try:
            memory_stats = stats.get('memory', {})
            if not isinstance(memory_stats, dict):
                return {'usage': 0, 'working_set': 0, 'rss': 0, 'cache': 0, 'swap': 0, 'mapped_file': 0, 'failcnt': 0}
            
            return {
                'usage': memory_stats.get('usage', 0),
                'working_set': memory_stats.get('working_set', 0),
                'rss': memory_stats.get('rss', 0),
                'cache': memory_stats.get('cache', 0),
                'swap': memory_stats.get('swap', 0),
                'mapped_file': memory_stats.get('mapped_file', 0),
                'failcnt': memory_stats.get('failcnt', 0)
            }
        except Exception as e:
            self.logger.warning(f"Erro ao extrair memory stats: {e}")
            return {'usage': 0, 'working_set': 0, 'rss': 0, 'cache': 0, 'swap': 0, 'mapped_file': 0, 'failcnt': 0}
    
    def _extract_network_stats(self, stats: Dict) -> Dict:
        """Extrai métricas de rede com validação"""
        try:
            network_stats = stats.get('network', {})
            if not isinstance(network_stats, dict):
                return {'rx_bytes': 0, 'tx_bytes': 0, 'rx_packets': 0, 'tx_packets': 0, 'rx_errors': 0, 'tx_errors': 0, 'interfaces_count': 0}
            
            interfaces = network_stats.get('interfaces', [])
            if not isinstance(interfaces, list):
                interfaces = []
            
            totals = {'rx_bytes': 0, 'tx_bytes': 0, 'rx_packets': 0, 'tx_packets': 0, 'rx_errors': 0, 'tx_errors': 0}
            
            for iface in interfaces:
                if isinstance(iface, dict):
                    for key in totals.keys():
                        totals[key] += iface.get(key, 0)
            
            totals['interfaces_count'] = len(interfaces)
            return totals
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair network stats: {e}")
            return {'rx_bytes': 0, 'tx_bytes': 0, 'rx_packets': 0, 'tx_packets': 0, 'rx_errors': 0, 'tx_errors': 0, 'interfaces_count': 0}
    
    def _extract_filesystem_stats(self, stats: Dict) -> Dict:
        """Extrai métricas do sistema de arquivos com validação"""
        try:
            filesystem_stats = stats.get('filesystem', [])
            if not isinstance(filesystem_stats, list):
                filesystem_stats = []
            
            totals = {'total_usage': 0, 'total_capacity': 0, 'total_available': 0, 'filesystems_count': 0}
            
            for fs in filesystem_stats:
                if isinstance(fs, dict):
                    totals['total_usage'] += fs.get('usage', 0)
                    totals['total_capacity'] += fs.get('capacity', 0)
                    totals['total_available'] += fs.get('available', 0)
                    totals['filesystems_count'] += 1
            
            totals['usage_percentage'] = (totals['total_usage'] / totals['total_capacity'] * 100) if totals['total_capacity'] > 0 else 0
            return totals
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair filesystem stats: {e}")
            return {'total_usage': 0, 'total_capacity': 0, 'total_available': 0, 'filesystems_count': 0, 'usage_percentage': 0}
    
    def collect_single_snapshot(self) -> List[Dict]:
        """Coleta um snapshot único de métricas para teste"""
        self.logger.info("Coletando snapshot único de métricas")
        
        # Executar debug se habilitado
        if self.debug_mode:
            self.debug_api_structure()
        
        containers_data = self.get_containers_info(count=1)
        if not containers_data:
            self.logger.warning("Nenhum dado disponível")
            return []
        
        metrics_data = []
        for container_path, container_info in containers_data.items():
            try:
                if not isinstance(container_info, dict):
                    continue
                    
                stats_list = container_info.get('stats', [])
                if not isinstance(stats_list, list) or not stats_list:
                    continue
                
                latest_stat = stats_list[-1]
                if not isinstance(latest_stat, dict):
                    continue
                
                metric_entry = {
                    'collection_timestamp': datetime.now().isoformat(),
                    'stat_timestamp': latest_stat.get('timestamp'),
                    'container_path': container_path,
                    'container_name': self._extract_container_name(container_path, container_info),
                    'cpu_usage': self._extract_cpu_usage(latest_stat),
                    'memory_usage': self._extract_memory_usage(latest_stat),
                    'network_stats': self._extract_network_stats(latest_stat),
                    'filesystem_stats': self._extract_filesystem_stats(latest_stat)
                }
                metrics_data.append(metric_entry)
                
            except Exception as e:
                self.logger.error(f"Erro ao processar {container_path}: {e}")
        
        self.logger.info(f"Snapshot coletado: {len(metrics_data)} containers")
        return metrics_data