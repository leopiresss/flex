from flask import render_template_string
from flask import Flask, jsonify, request
from datetime import datetime
import psutil
import time
import threading
import random
import os
import csv
import socket
import os

app = Flask(__name__)


# Caminho do arquivo de log
MEMORY_LOG_FILE = 'memory_leak_log.csv'

# Lock para escrita thread-safe no CSV
csv_lock = threading.Lock()

# Variáveis globais para controlar degradação
leaked_memory = []
cpu_stress_active = False
io_stress_active = False
network_delay = 0

# Flag para controlar o leak
leak_active = False
leak_thread = None


# Add after the imports and before other routes

@app.route('/')
@app.route('/help')
def api_help():
    """Documentação das APIs disponíveis"""
    api_docs = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Degradation App API Help</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { margin-bottom: 20px; }
            .method { color: #0066cc; }
            .path { color: #333; font-weight: bold; }
            .description { color: #666; }
            h2 { color: #333; border-bottom: 1px solid #ccc; }
        </style>
    </head>
    <body>
        <h1>🔧 Degradation App API Documentation</h1>
        
        <h2>Health Check</h2>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/health</span>
            <p class="description">Verifica a saúde da aplicação</p>
        </div>

        <h2>Memory Stress</h2>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/memory/start</span>
            <p class="description">Inicia memory leak gradual com logging</p>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/memory/stop</span>
            <p class="description">Para o memory leak</p>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/memory/status</span>
            <p class="description">Retorna status detalhado do memory leak</p>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/memory/spike</span>
            <p class="description">Cria um spike repentino de memória</p>
        </div>

        <h2>Memory Logs</h2>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/memory/log/view</span>
            <p class="description">Visualiza logs de memory leak no navegador</p>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/memory/log/download</span>
            <p class="description">Download do arquivo de log CSV</p>
        </div>

        <h2>CPU Stress</h2>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/cpu/start</span>
            <p class="description">Inicia stress de CPU</p>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/cpu/stop</span>
            <p class="description">Para stress de CPU</p>
        </div>

        <h2>I/O Stress</h2>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/io/start</span>
            <p class="description">Inicia stress de I/O</p>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/io/stop</span>
            <p class="description">Para stress de I/O</p>
        </div>

        <h2>Network Stress</h2>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/network/delay/{ms}</span>
            <p class="description">Define latência de rede em milissegundos</p>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/api/data</span>
            <p class="description">Endpoint com latência configurável</p>
        </div>

        <h2>Metrics</h2>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/metrics</span>
            <p class="description">Expõe métricas da aplicação (CPU, memória)</p>
        </div>

        <h2>Combined Stress</h2>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/all/start</span>
            <p class="description">Inicia todos os tipos de stress</p>
        </div>
        <div class="endpoint">
            <span class="method">GET</span> 
            <span class="path">/stress/all/stop</span>
            <p class="description">Para todos os tipos de stress</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(api_docs)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/stress/memory/log/view')
def view_memory_log():
    """Exibe o conteúdo do arquivo de log no navegador com formatação melhorada"""
    if not os.path.exists(MEMORY_LOG_FILE):
        return jsonify({
            "error": "Log file not found",
            "message": "Start memory leak first to generate logs"
        }), 404
    
    with open(MEMORY_LOG_FILE, 'r') as f:
        csv_reader = csv.reader(f)
        headers = next(csv_reader)
        rows = list(csv_reader)
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pod Degradation Metrics Log</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .metrics-group { margin: 20px 0; }
            .group-title { 
                background: #f0f0f0;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
                color: #333;
            }
            table { 
                border-collapse: collapse; 
                width: 100%;
                margin-bottom: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            th, td { 
                border: 1px solid #ddd; 
                padding: 12px 8px; 
                text-align: left; 
            }
            th { 
                background-color: #4CAF50;
                color: white;
            }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f5f5f5; }
            .pod-info { color: #666; margin-bottom: 20px; }
            .refresh-btn {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin-bottom: 20px;
            }
            .refresh-btn:hover {
                background-color: #45a049;
            }
        </style>
        <script>
            function refreshPage() {
                location.reload();
            }
        </script>
    </head>
    <body>
        <h1>🔍 Pod Degradation Metrics Log</h1>
        <button onclick="refreshPage()" class="refresh-btn">🔄 Refresh Data</button>
        
        <div class="pod-info">
            <strong>Pod Name:</strong> {{ rows[-1][0] if rows else 'N/A' }}<br>
            <strong>Last Update:</strong> {{ rows[-1][1] if rows else 'N/A' }}
        </div>

        <table>
            <tr>
                <th colspan="999" class="group-title">📊 Memory Metrics</th>
            </tr>
            <tr>
                <th>Time</th>
                <th>Used (MB)</th>
                <th>Available (MB)</th>
                <th>Total (MB)</th>
                <th>Usage %</th>
                <th>Leaked (MB)</th>
                <th>RSS (MB)</th>
                <th>VMS (MB)</th>
                <th>Shared (MB)</th>
                <th>Page Faults</th>
                <th>Page Faults Δ</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row[1].split('T')[1] }}</td>
                <td>{{ row[2] }}</td>
                <td>{{ row[3] }}</td>
                <td>{{ row[4] }}</td>
                <td>{{ row[5] }}</td>
                <td>{{ row[6] }}</td>
                <td>{{ row[7] }}</td>
                <td>{{ row[8] }}</td>
                <td>{{ row[9] }}</td>
                <td>{{ row[10] }}</td>
                <td>{{ row[11] }}</td>
            </tr>
            {% endfor %}
        </table>

        <table>
            <tr>
                <th colspan="999" class="group-title">💻 CPU Metrics</th>
            </tr>
            <tr>
                <th>Time</th>
                <th>CPU %</th>
                <th>User Time</th>
                <th>System Time</th>
                <th>IO Wait</th>
                <th>Context Switches</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row[1].split('T')[1] }}</td>
                <td>{{ row[12] }}</td>
                <td>{{ row[13] }}</td>
                <td>{{ row[14] }}</td>
                <td>{{ row[15] }}</td>
                <td>{{ row[16] }}</td>
            </tr>
            {% endfor %}
        </table>

        <table>
            <tr>
                <th colspan="999" class="group-title">💾 I/O Metrics</th>
            </tr>
            <tr>
                <th>Time</th>
                <th>Read Count</th>
                <th>Write Count</th>
                <th>Read Bytes</th>
                <th>Write Bytes</th>
                <th>Read Time (ms)</th>
                <th>Write Time (ms)</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row[1].split('T')[1] }}</td>
                <td>{{ row[17] }}</td>
                <td>{{ row[18] }}</td>
                <td>{{ row[19] }}</td>
                <td>{{ row[20] }}</td>
                <td>{{ row[21] }}</td>
                <td>{{ row[22] }}</td>
            </tr>
            {% endfor %}
        </table>

        <table>
            <tr>
                <th colspan="999" class="group-title">🌐 Network Metrics</th>
            </tr>
            <tr>
                <th>Time</th>
                <th>Bytes Sent</th>
                <th>Bytes Recv</th>
                <th>Packets Sent</th>
                <th>Packets Recv</th>
                <th>Errors In</th>
                <th>Errors Out</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row[1].split('T')[1] }}</td>
                <td>{{ row[23] }}</td>
                <td>{{ row[24] }}</td>
                <td>{{ row[25] }}</td>
                <td>{{ row[26] }}</td>
                <td>{{ row[27] }}</td>
                <td>{{ row[28] }}</td>
            </tr>
            {% endfor %}
        </table>

        <table>
            <tr>
                <th colspan="999" class="group-title">📝 Process Metrics</th>
            </tr>
            <tr>
                <th>Time</th>
                <th>Threads</th>
                <th>Open Files</th>
                <th>Connections</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row[1].split('T')[1] }}</td>
                <td>{{ row[29] }}</td>
                <td>{{ row[30] }}</td>
                <td>{{ row[31] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    
    return render_template_string(html_template, rows=rows)

def init_memory_log():
    """Inicializa o arquivo CSV de log com métricas completas de degradação"""
    with open(MEMORY_LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            # Pod Info
            'pod_name',
            'timestamp_iso',
            
            # Memory Metrics
            'memory_used_mb',
            'memory_available_mb',
            'memory_total_mb',
            'memory_percent',
            'memory_leaked_mb',
            'memory_rss_mb',
            'memory_vms_mb',
            'memory_shared_mb',
            'memory_page_faults',
            'memory_page_faults_delta',
            
            # CPU Metrics
            'cpu_percent',
            'cpu_user_time',
            'cpu_system_time',
            'cpu_iowait',
            'cpu_ctx_switches',
            
            # I/O Metrics
            'io_read_count',
            'io_write_count',
            'io_read_bytes',
            'io_write_bytes',
            'io_read_time_ms',
            'io_write_time_ms',
            
            # Network Metrics
            'net_bytes_sent',
            'net_bytes_recv',
            'net_packets_sent',
            'net_packets_recv',
            'net_errin',
            'net_errout',
            
            # Process Metrics
            'process_threads',
            'process_open_files',
            'process_connections'
        ])

def log_memory_usage(leaked_mb, leaked_count, leak_rate=0):
    """Registra métricas detalhadas de degradação do pod"""
    now = datetime.now()
    pod_name = os.getenv('HOSTNAME', socket.gethostname())
    
    # Process metrics
    process = psutil.Process()
    process_mem = process.memory_info()
    
    # System metrics
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_times_percent()
    io_counters = psutil.disk_io_counters()
    net_counters = psutil.net_io_counters()
    
    # Calculate deltas for page faults
    current_faults = process_mem.pfaults if hasattr(process_mem, 'pfaults') else 0
    
    log_data = [
        # Pod Info
        pod_name,
        now.isoformat(),
        
        # Memory Metrics
        f"{mem.used / 1024 / 1024:.2f}",
        f"{mem.available / 1024 / 1024:.2f}",
        f"{mem.total / 1024 / 1024:.2f}",
        f"{mem.percent:.2f}",
        f"{leaked_mb:.2f}",
        f"{process_mem.rss / 1024 / 1024:.2f}",
        f"{process_mem.vms / 1024 / 1024:.2f}",
        f"{getattr(process_mem, 'shared', 0) / 1024 / 1024:.2f}",
        current_faults,
        current_faults - getattr(log_memory_usage, 'last_faults', 0),
        
        # CPU Metrics
        f"{process.cpu_percent():.2f}",
        f"{cpu.user:.2f}",
        f"{cpu.system:.2f}",
        f"{cpu.iowait:.2f}",
        process.num_ctx_switches(),
        
        # I/O Metrics
        io_counters.read_count,
        io_counters.write_count,
        io_counters.read_bytes,
        io_counters.write_bytes,
        io_counters.read_time,
        io_counters.write_time,
        
        # Network Metrics
        net_counters.bytes_sent,
        net_counters.bytes_recv,
        net_counters.packets_sent,
        net_counters.packets_recv,
        net_counters.errin,
        net_counters.errout,
        
        # Process Metrics
        len(process.threads()),
        len(process.open_files()),
        len(process.connections())
    ]
    
    # Store last faults for delta calculation
    log_memory_usage.last_faults = current_faults
    
    # Write to CSV thread-safe
    with csv_lock:
        with open(MEMORY_LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(log_data)

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
    """Inicia memory leak gradual com logging detalhado em CSV"""
    global leak_active, leak_thread
    
    if leak_active:
        return jsonify({
            "status": "already running",
            "message": "Memory leak is already active"
        }), 400
    
    # Inicializar arquivo de log
    init_memory_log()
    
    leak_active = True
    start_time = time.time()
    last_size = 0
    
    def leak():
        nonlocal last_size
        
        while leak_active:
            # Adicionar bloco de memória (~800KB)
            leaked_memory.append([0] * 100000)
            
            # Calcular memória vazada
            leaked_count = len(leaked_memory)
            leaked_mb = leaked_count * 0.8
            
            # Calcular taxa de vazamento
            elapsed = time.time() - start_time
            leak_rate = (leaked_mb - last_size) if elapsed > 0 else 0
            last_size = leaked_mb
            
            # Registrar no CSV
            log_memory_usage(leaked_mb, leaked_count, leak_rate)
            
            # Log no console a cada 10 iterações
            if leaked_count % 10 == 0:
                print(f"💧 Memory Leak: {leaked_mb:.2f} MB ({leaked_count} blocks)")
            
            # Aguardar 1 segundo
            time.sleep(1)
    
    # Iniciar thread do memory leak
    leak_thread = threading.Thread(target=leak, daemon=True)
    leak_thread.start()
    
    return jsonify({
        "status": "memory leak started",
        "log_file": MEMORY_LOG_FILE,
        "message": "Memory usage is being logged to CSV every second",
        "leak_rate_mb_per_sec": 0.8
    }), 200

@app.route('/stress/memory/stop')
def stop_memory_leak():
    """Para o memory leak e salva estatísticas finais"""
    global leak_active
    
    if not leak_active:
        return jsonify({
            "status": "not running",
            "message": "No active memory leak to stop"
        }), 400
    
    leak_active = False
    
    leaked_count = len(leaked_memory)
    leaked_mb = leaked_count * 0.8
    
    # Log final antes de limpar
    log_memory_usage(leaked_mb, leaked_count, 0)
    
    # Limpar memória
    leaked_memory.clear()
    
    return jsonify({
        "status": "memory leak stopped",
        "cleared_memory_mb": leaked_mb,
        "cleared_blocks": leaked_count,
        "log_file": MEMORY_LOG_FILE
    }), 200

@app.route('/stress/memory/status')
def memory_leak_status():
    """Retorna status atual detalhado do memory leak"""
    mem = psutil.virtual_memory()
    process = psutil.Process()
    
    leaked_count = len(leaked_memory)
    leaked_mb = leaked_count * 0.8
    
    return jsonify({
        "leak_active": leak_active,
        "leaked_memory_mb": leaked_mb,
        "leaked_blocks": leaked_count,
        "system": {
            "memory_used_mb": mem.used / 1024 / 1024,
            "memory_percent": mem.percent,
            "memory_available_mb": mem.available / 1024 / 1024,
            "memory_total_mb": mem.total / 1024 / 1024
        },
        "process": {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent()
        },
        "log_file": MEMORY_LOG_FILE
    }), 200

@app.route('/stress/memory/log/download')
def download_memory_log():
    """Permite download do arquivo de log CSV"""
    from flask import send_file
    
    if os.path.exists(MEMORY_LOG_FILE):
        return send_file(
            MEMORY_LOG_FILE,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'memory_leak_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    else:
        return jsonify({
            "error": "Log file not found",
            "message": "Start memory leak first to generate logs"
        }), 404
    
    
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