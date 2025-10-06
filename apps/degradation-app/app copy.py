from flask import Flask, jsonify, request
import psutil
import time
import threading
import random
import os

app = Flask(__name__)

# Variáveis globais para controlar degradação
leaked_memory = []
cpu_stress_active = False
io_stress_active = False
network_delay = 0



@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/metrics')
def metrics():
    """Expõe métricas customizadas da aplicação"""
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    
    return jsonify({
        "memory_percent": mem.percent,
        "memory_used_mb": mem.used / 1024 / 1024,
        "cpu_percent": cpu,
        "leaked_memory_mb": len(leaked_memory) * 0.8  # Aproximado
    })

@app.route('/stress/memory/start')
def start_memory_leak():
    """Inicia memory leak gradual"""
    def leak():
        while True:
            leaked_memory.append([0] * 100000)  # ~800KB
            time.sleep(1)
    
    threading.Thread(target=leak, daemon=True).start()
    return jsonify({"status": "memory leak started"}), 200

@app.route('/stress/memory/spike')
def memory_spike():
    """Cria um spike repentino de memória"""
    spike_data = []
    for _ in range(100):
        spike_data.append([0] * 1000000)  # ~8MB cada
    
    time.sleep(5)  # Mantém por 5 segundos
    spike_data.clear()
    
    return jsonify({"status": "memory spike completed"}), 200

@app.route('/stress/cpu/start')
def start_cpu_stress():
    """Inicia stress de CPU"""
    global cpu_stress_active
    cpu_stress_active = True
    
    def burn_cpu():
        while cpu_stress_active:
            _ = sum(range(1000000))
    
    # Iniciar múltiplas threads de CPU
    for _ in range(4):
        threading.Thread(target=burn_cpu, daemon=True).start()
    
    return jsonify({"status": "cpu stress started"}), 200

@app.route('/stress/cpu/stop')
def stop_cpu_stress():
    """Para stress de CPU"""
    global cpu_stress_active
    cpu_stress_active = False
    return jsonify({"status": "cpu stress stopped"}), 200

@app.route('/stress/io/start')
def start_io_stress():
    """Inicia stress de I/O"""
    global io_stress_active
    io_stress_active = True
    
    def stress_io():
        while io_stress_active:
            with open('/tmp/stress_test.dat', 'a') as f:
                f.write('x' * 1024 * 1024)  # 1MB por vez
            time.sleep(0.5)
    
    threading.Thread(target=stress_io, daemon=True).start()
    return jsonify({"status": "io stress started"}), 200

@app.route('/stress/io/stop')
def stop_io_stress():
    """Para stress de I/O"""
    global io_stress_active
    io_stress_active = False
    # Limpar arquivo
    if os.path.exists('/tmp/stress_test.dat'):
        os.remove('/tmp/stress_test.dat')
    return jsonify({"status": "io stress stopped"}), 200

@app.route('/stress/network/delay/<int:ms>')
def set_network_delay(ms):
    """Simula latência de rede"""
    global network_delay
    network_delay = ms / 1000.0
    return jsonify({"status": f"network delay set to {ms}ms"}), 200

@app.route('/api/data')
def get_data():
    """Endpoint com latência configurável"""
    if network_delay > 0:
        time.sleep(network_delay)
    
    # Simular processamento
    data = {
        "timestamp": time.time(),
        "random_data": [random.randint(1, 100) for _ in range(100)]
    }
    
    return jsonify(data), 200

@app.route('/stress/all/start')
def start_all_stress():
    """Inicia todos os tipos de stress"""
    start_memory_leak()
    start_cpu_stress()
    start_io_stress()
    set_network_delay(100)
    return jsonify({"status": "all stress started"}), 200

@app.route('/stress/all/stop')
def stop_all_stress():
    """Para todos os tipos de stress"""
    global cpu_stress_active, io_stress_active, network_delay
    cpu_stress_active = False
    io_stress_active = False
    network_delay = 0
    leaked_memory.clear()
    return jsonify({"status": "all stress stopped"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)