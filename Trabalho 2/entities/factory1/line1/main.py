import time
from shared.mqtt_client import get_client

# --- Configurações da Linha ---
# Flag para controlar o estado da produção
production_halted = False
PART_NAME = "Parte A"
REQUEST_QUANTITY = 5
REQUEST_INTERVAL_SECONDS = 5

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[LINE1] Falha ao conectar: {reason_code}")
    else:
        print("[LINE1] Conectado ao broker MQTT")
        # Se inscreve no tópico de status do estoque para saber quando parar/retomar
        client.subscribe("estoque/status")

def on_message(client, userdata, msg):
    """Processa mensagens de status do almoxarifado."""
    global production_halted
    payload = msg.payload.decode('utf-8')
    
    try:
        part_name, status = payload.split(':')
        
        # Verifica se a mensagem é para a peça que esta linha utiliza
        if part_name.strip() == PART_NAME:
            if status.strip() == "OUT_OF_STOCK" and not production_halted:
                print("[LINE1] AVISO: Estoque insuficiente no almoxarifado. Produção parada.")
                production_halted = True
            elif status.strip() == "STOCK_OK" and production_halted:
                print("[LINE1] INFO: Estoque normalizado. Retomando produção.")
                production_halted = False
    except (ValueError, IndexError):
        # Ignora mensagens mal formatadas
        pass

client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
client.loop_start()

# Uma pequena pausa para garantir que a conexão em background seja estabelecida
time.sleep(1) 

print("[LINE1] Iniciando ciclo de produção.")
while True:
    if not production_halted:
        print(f"[LINE1] Solicitando {REQUEST_QUANTITY} unidades de {PART_NAME} do almoxarifado...")
        client.publish("estoque/check_out", f"{PART_NAME}: {REQUEST_QUANTITY}")
    else:
        print("[LINE1] Produção parada, aguardando normalização do estoque.")
    
    time.sleep(REQUEST_INTERVAL_SECONDS)
