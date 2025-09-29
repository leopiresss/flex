from flask import Flask, jsonify, request
import time
import csv
import os
from datetime import datetime
import math
import threading
import logging

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postgres_stress_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Lock para sincronizar escrita no arquivo de log
log_lock = threading.Lock()

def is_prime(n):
    """
    Verifica se um número é primo usando teste de primalidade otimizado.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Verifica divisores ímpares até a raiz quadrada de n
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

def generate_primes(count):
    """
    Gera uma lista com os primeiros 'count' números primos.
    """
    primes = []
    num = 2
    
    while len(primes) < count:
        if is_prime(num):
            primes.append(num)
        num += 1
    
    return primes



def log_to_csv(start_time, end_time, duration_ms, prime_count):
    """
    Grava informações da execução no arquivo de log CSV.
    """
    log_file = 'prime_server_log.csv'
    
    # Verifica se o arquivo existe, se não, cria com cabeçalho
    file_exists = os.path.isfile(log_file)
    
    with log_lock:
        with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp_inicio', 'timestamp_fim', 'duracao_ms', 'qtd_primos_gerados']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'timestamp_inicio': start_time,
                'timestamp_fim': end_time,
                'duracao_ms': duration_ms,
                'qtd_primos_gerados': prime_count
            })

@app.route('/primes', methods=['GET'])
def get_primes():
    """
    Endpoint para gerar números primos.
    Parâmetro: count (quantidade de números primos desejados)
    """
    try:
        # Captura o timestamp de início
        start_time =  time.time()
        start_timestamp = int(start_time * 1000)  # timestamp em milissegundos
        
        # Obtém o parâmetro 'count' da query string
        count = request.args.get('count', type=int)
        
        if count is None:
            return jsonify({
                'error': 'Parâmetro "count" é obrigatório',
                'exemplo': '/primes?count=10'
            }), 400
        
        if count <= 0:
            return jsonify({
                'error': 'O parâmetro "count" deve ser um número positivo'
            }), 400
        
        if count > 100000:
            return jsonify({
                'error': 'Limite máximo de 10.000 números primos por requisição'
            }), 400
        
        # Gera os números primos
        prime_list = generate_primes(count)
        
        # Captura o timestamp de fim
        end_time = time.time()
        end_timestamp = int(end_time * 1000)  # timestamp em milissegundos
        
        # Calcula a duração em milissegundos
        duration_ms = int((end_time - start_time) * 1000)
        dt_start_time =  time.strftime("%d/%m/%Y %H:%M:%S")
        dt_end_time =  time.strftime("%d/%m/%Y %H:%M:%S")
        print(dt_start_time)                               
        # Grava no log
        log_to_csv(dt_start_time, dt_end_time, duration_ms, len(prime_list))
        
        # Prepara a resposta JSON
     
        
        response = {
            'qtd_numeros_primos': len(prime_list),
            'lista_numeros_primos': prime_list,
            'duracao_execucao_ms': duration_ms,
            'dt_inicio': f'{dt_start_time}'
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Erro interno do servidor: {str(e)}'
        }), 500

@app.route('/primes/<int:count>', methods=['GET'])
def get_primes_by_path(count):
    """
    Endpoint alternativo para gerar números primos usando parâmetro na URL.
    """
    try:
        start_time = time.time()
        start_timestamp = int(start_time * 1000)
        
        if count <= 0:
            return jsonify({
                'error': 'O parâmetro "count" deve ser um número positivo'
            }), 400
        
        if count > 10000:
            return jsonify({
                'error': 'Limite máximo de 10.000 números primos por requisição'
            }), 400
        
        prime_list = generate_primes(count)
        
        end_time = time.time()
        end_timestamp = int(end_time * 1000)
        duration_ms = int((end_time - start_time) * 1000)
        
        log_to_csv(start_timestamp, end_timestamp, duration_ms, len(prime_list))



        response = {
            'qtd_numeros_primos': len(prime_list),
            'lista_numeros_primos': prime_list,
            'duracao_execucao_ms': duration_ms,
            'timestamp_execucao': start_timestamp
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Erro interno do servidor: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de verificação de saúde do servidor.
    """
    return jsonify({
        'status': 'ok',
        'timestamp': int(time.time() * 1000),
        'message': 'Servidor de números primos funcionando'
    }), 200

@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Endpoint para visualizar os logs gerados.
    """
    try:
        log_file = 'prime_server_log.csv'
        
        if not os.path.isfile(log_file):
            return jsonify({
                'message': 'Nenhum log encontrado ainda'
            }), 200
        
        logs = []
        with open(log_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                logs.append(row)
        
        return jsonify({
            'total_logs': len(logs),
            'logs': logs[-50:]  # Retorna os últimos 50 logs
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Erro ao ler logs: {str(e)}'
        }), 500

@app.route('/', methods=['GET'])
def home():
    """
    Página inicial com instruções de uso.
    """
    return jsonify({
        'nome': 'Servidor de Teste de Stress - Gerador de Números Primos',
        'versao': '1.0',
        'endpoints': {
            'GET /primes?count=N': 'Gera N números primos (via query string)',
            'GET /primes/N': 'Gera N números primos (via parâmetro na URL)',
            'GET /health': 'Verificação de saúde do servidor',
            'GET /logs': 'Visualiza os últimos logs gerados',
            'GET /': 'Esta página de ajuda'
        },
        'exemplos': [
            'GET /primes?count=10',
            'GET /primes/50',
            'GET /health'
        ],
        'limite_maximo': '10.000 números primos por requisição'
    }), 200

if __name__ == '__main__':
    print("🚀 Iniciando servidor de teste de stress - Gerador de Números Primos")
    print("📊 Logs serão salvos em: prime_server_log.csv")
    print("🌐 Endpoints disponíveis:")
    print("   GET /primes?count=N")
    print("   GET /primes/N")
    print("   GET /health")
    print("   GET /logs")
    print("   GET /")
    print("\n💡 Exemplo de uso:")
    print("   curl 'http://localhost:5001/primes?count=100'")
    print("   curl 'http://localhost:5001/primes/50'")
    print("\n" + "="*50)
    
    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=7071, debug=False, threaded=True)