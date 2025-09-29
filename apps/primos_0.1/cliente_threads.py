#!/usr/bin/env python3
"""
Servidor HTTP Multi-threaded
Recebe número de threads como parâmetro e faz requisições concorrentes a uma URL
"""

import argparse
import threading
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

url_default = 'http://192.168.242.134:7071/primes?count=10000'

class ThreadedRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, target_url=url_default, **kwargs):
        self.target_url = target_url
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Manipula requisições GET"""
        try:
            # Parse da URL e parâmetros
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Obtém o número de threads (padrão: 1)
            num_threads = int(query_params.get('threads', [1])[0])
            
            # Limita o número máximo de threads por segurança
            max_threads = 50
            if num_threads > max_threads:
                num_threads = max_threads
                logger.warning(f"Número de threads limitado a {max_threads}")
            
            # Executa as requisições com threads
            results = self.execute_threaded_requests(num_threads)
            
            # Prepara resposta
            response_data = {
                "threads_used": num_threads,
                "target_url": self.target_url,
                "results": results,
                "summary": {
                    "successful_requests": len([r for r in results if r["success"]]),
                    "failed_requests": len([r for r in results if not r["success"]]),
                    "average_response_time": sum([r["response_time"] for r in results if r["success"]]) / max(1, len([r for r in results if r["success"]]))
                }
            }
            
            # Envia resposta
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except ValueError as e:
            self.send_error(400, f"Parâmetro inválido: {e}")
        except Exception as e:
            logger.error(f"Erro interno: {e}")
            self.send_error(500, f"Erro interno do servidor: {e}")
    
    def do_POST(self):
        """Manipula requisições POST para configurar URL alvo"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if 'target_url' in data:
                self.target_url = data['target_url']
                
                response = {
                    "message": "URL alvo atualizada com sucesso",
                    "new_target_url": self.target_url
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_error(400, "Campo 'target_url' é obrigatório")
                
        except json.JSONDecodeError:
            self.send_error(400, "JSON inválido")
        except Exception as e:
            logger.error(f"Erro no POST: {e}")
            self.send_error(500, f"Erro interno: {e}")
    
    def execute_threaded_requests(self, num_threads):
        """Executa requisições usando múltiplas threads"""
        results = []
        threads = []
        results_lock = threading.Lock()
        
        def make_request(thread_id):
            """Função executada por cada thread"""
            start_time = time.time()
            try:
                logger.info(f"Thread {thread_id}: Iniciando requisição para {self.target_url}")
                response = requests.get(self.target_url, timeout=30)
                end_time = time.time()
                
                result = {
                    "thread_id": thread_id,
                    "success": True,
                    "status_code": response.status_code,
                    "response_time": round(end_time - start_time, 3),
                    "content_length": len(response.content),
                    "url": self.target_url
                }
                
                logger.info(f"Thread {thread_id}: Sucesso - {response.status_code} - {result['response_time']}s")
                
            except requests.exceptions.RequestException as e:
                end_time = time.time()
                result = {
                    "thread_id": thread_id,
                    "success": False,
                    "error": str(e),
                    "response_time": round(end_time - start_time, 3),
                    "url": self.target_url
                }
                logger.error(f"Thread {thread_id}: Erro - {e}")
            
            # Thread-safe addition to results
            with results_lock:
                results.append(result)
        
        # Cria e inicia as threads
        start_time = time.time()
        for i in range(num_threads):
            thread = threading.Thread(target=make_request, args=(i + 1,))
            threads.append(thread)
            thread.start()
        
        # Aguarda todas as threads terminarem
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        logger.info(f"Todas as {num_threads} threads completadas em {total_time:.3f}s")
        
        return sorted(results, key=lambda x: x["thread_id"])
    
    def log_message(self, format, *args):
        """Override para usar o logger personalizado"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def create_handler(target_url):
    """Factory function para criar handler com URL alvo configurada"""
    def handler(*args, **kwargs):
        return ThreadedRequestHandler(*args, target_url=target_url, **kwargs)
    return handler

def main():
    parser = argparse.ArgumentParser(description='Servidor HTTP Multi-threaded')
    parser.add_argument('--port', '-p', type=int, default=7073, 
                       help='Porta do servidor (padrão: 7073)')
    parser.add_argument('--target-url', '-u', type=str, 
                       default=url_default,
                       help='URL alvo para as requisições (padrão: {url_default})')
    parser.add_argument('--host', type=str, default='localhost',
                       help='Host do servidor (padrão: localhost)')
    
    args = parser.parse_args()
    
    # Cria o handler com a URL alvo
    handler = create_handler(args.target_url)
    
    # Configura e inicia o servidor
    server = HTTPServer((args.host, args.port), handler)
    
    print(f"\n🚀 Servidor Multi-threaded iniciado!")
    print(f"📍 Endereço: http://{args.host}:{args.port}")
    print(f"🎯 URL alvo: {args.target_url}")
    print(f"\n📖 Como usar:")
    print(f"  GET  /?threads=N        - Faz N requisições concorrentes")
    print(f"  POST /                  - Atualiza URL alvo: {{'target_url': 'nova_url'}}")
    print(f"\n💡 Exemplos:")
    print(f"  curl 'http://{args.host}:{args.port}/?threads=5'")
    print(f"  curl -X POST -H 'Content-Type: application/json' -d '{{'target_url':'http://example.com'}}' http://{args.host}:{args.port}")
    print(f"\n⏹️  Pressione Ctrl+C para parar\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹️  Servidor interrompido pelo usuário")
        server.shutdown()
        server.server_close()
        print("✅ Servidor encerrado com sucesso")

if __name__ == '__main__':
    main()