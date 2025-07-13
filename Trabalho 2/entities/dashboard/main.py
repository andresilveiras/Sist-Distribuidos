from flask import Flask, render_template
from flask_socketio import SocketIO
from shared.mqtt_client import get_client
from shared.products import ALL_PARTS

# --- Configuração do Flask e SocketIO ---
app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

# --- Estado do Sistema ---
# Dicionário para armazenar o estado de cada peça no inventário
inventory_state = {
    part: {"quantity": 100, "status": "VERDE"} for part in ALL_PARTS
}
# Dicionário para armazenar o estado de cada linha de produção
lines_state = {}

# --- Funções Auxiliares ---
def calculate_and_emit_inventory_summary():
    """Calcula a contagem de itens por status e emite para todos os clientes."""
    counts = {"VERDE": 0, "AMARELO": 0, "VERMELHO": 0}
    for part_data in inventory_state.values():
        status = part_data.get("status", "VERDE")
        if status in counts:
            counts[status] += 1
    socketio.emit('inventory_summary_update', counts)

# --- Lógica do MQTT ---
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[DASHBOARD] Falha ao conectar ao MQTT: {reason_code}")
        return
    print("[DASHBOARD] Conectado ao broker MQTT. Inscrevendo-se nos tópicos de dashboard.")
    # Se inscreve em todos os tópicos de atualização do dashboard
    client.subscribe("dashboard/inventory/+")
    client.subscribe("dashboard/lines/+")

def on_message(client, userdata, msg):
    topic_parts = msg.topic.split('/')
    payload = msg.payload.decode('utf-8')

    # Atualização do inventário
    if topic_parts[1] == 'inventory':
        part_name = topic_parts[2]
        if part_name in inventory_state:
            try:
                quantity, status = payload.split(':')
                inventory_state[part_name] = {"quantity": int(quantity), "status": status}
                # Emite a atualização para os clientes web
                socketio.emit('inventory_update', {
                    'part_name': part_name,
                    'quantity': int(quantity),
                    'status': status
                })
                # Recalcula e emite o resumo do inventário
                calculate_and_emit_inventory_summary()
            except (ValueError, IndexError):
                print(f"[DASHBOARD] Mensagem de inventário mal formatada: {payload}")

    # Atualização das linhas de produção
    elif topic_parts[1] == 'lines':
        line_id = topic_parts[2]
        try:
            product_id, completed, total, status_text = payload.split(':')
            lines_state[line_id] = {
                'product_id': product_id,
                'completed': int(completed),
                'total': int(total),
                'status_text': status_text
            }
            # Emite a atualização para os clientes web
            socketio.emit('line_update', {'line_id': line_id, **lines_state[line_id]})
        except (ValueError, IndexError):
            print(f"[DASHBOARD] Mensagem de linha mal formatada: {payload}")

# --- Rotas e Eventos do SocketIO ---
@app.route('/')
def index():
    """ Serve a página principal do dashboard. """
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """ Quando um novo cliente web se conecta, envia o estado completo atual. """
    print("[DASHBOARD] Novo cliente web conectado. Enviando estado inicial.")
    # Envia o estado do inventário e das linhas
    socketio.emit('initial_state', {'inventory': inventory_state, 'lines': lines_state})
    # Envia o resumo inicial do inventário para o novo cliente
    calculate_and_emit_inventory_summary()

def mqtt_thread_function():
    """Função que será executada em background para o cliente MQTT."""
    mqtt_client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
    print("[DASHBOARD] Iniciando o loop do cliente MQTT.")
    mqtt_client.loop_forever()

# Inicia a tarefa de background do MQTT gerenciada pelo SocketIO
socketio.start_background_task(target=mqtt_thread_function)