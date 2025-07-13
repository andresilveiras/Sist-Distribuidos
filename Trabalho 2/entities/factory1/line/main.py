import time
import os
import sys
from shared.mqtt_client import get_client
from shared.products import BOM

# --- Configurações da Linha ---
LINE_ID = os.getenv("LINE_ID", "Desconhecida")
PRODUCT_ID = os.getenv("PRODUCT_ID")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "60"))

if not PRODUCT_ID or PRODUCT_ID not in BOM:
    print(f"[LINE {LINE_ID}] ERRO: Variável de ambiente PRODUCT_ID inválida ou não definida.")
    sys.exit(1)

# --- Estado da Linha ---
production_halted = False
start_new_batch = True # Flag para controlar o início de um novo lote

def publish_line_status(client, current_batch_count, status_text):
    """Publica o estado atual da linha para o dashboard."""
    payload = f"{PRODUCT_ID}:{current_batch_count}:{BATCH_SIZE}:{status_text}"
    client.publish(f"dashboard/lines/{LINE_ID}", payload, retain=True)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[LINE {LINE_ID}] Falha ao conectar: {reason_code}")
    else:
        print(f"[LINE {LINE_ID}] Conectado ao broker MQTT. Produzindo {BATCH_SIZE} unidades de {PRODUCT_ID}.")
        # Se inscreve no tópico de status do estoque para saber quando parar/retomar
        client.subscribe("estoque/status")
        # Se inscreve no tópico de "novo dia" para iniciar um novo lote
        client.subscribe("simulation/new_day")
        publish_line_status(client, 0, "Aguardando início do dia")

def on_message(client, userdata, msg):
    """Processa mensagens de status do almoxarifado."""
    global production_halted, start_new_batch
    payload = msg.payload.decode('utf-8')
    
    if msg.topic == "simulation/new_day":
        print(f"[LINE {LINE_ID}] Sinal de 'novo dia' recebido. Iniciando novo lote de produção.")
        start_new_batch = True
    elif msg.topic == "estoque/status":
        try:
            part_name, status = payload.split(':')
            part_name = part_name.strip()
            status = status.strip()
            
            if status == "OUT_OF_STOCK" and not production_halted:
                print(f"[LINE {LINE_ID}] AVISO: Estoque de '{part_name}' insuficiente. Produção parada.")
                production_halted = True
                # O status do dashboard será atualizado no loop principal

            elif status == "STOCK_OK" and production_halted:
                print(f"[LINE {LINE_ID}] INFO: Estoque normalizado. Retomando produção.")
                production_halted = False

        except (ValueError, IndexError):
            pass # Ignora mensagens mal formatadas

def run_production_batch(client):
    """Executa a lógica de produção para um lote completo."""
    global production_halted
    current_batch_count = 0
    
    while current_batch_count < BATCH_SIZE:
        parts_needed_for_current_unit = set(BOM[PRODUCT_ID])
        publish_line_status(client, current_batch_count, "Produzindo")

        while parts_needed_for_current_unit:
            if production_halted:
                part_name_faltando = next(iter(parts_needed_for_current_unit)) # Apenas para exibir
                publish_line_status(client, current_batch_count, f"Parada - Falta {part_name_faltando}")
                time.sleep(5)
                continue

            part_to_request = parts_needed_for_current_unit.pop()
            client.publish("estoque/check_out", f"{part_to_request}:1")
            time.sleep(0.5)

        current_batch_count += 1
        print(f"[LINE {LINE_ID}] PRODUTO {PRODUCT_ID} MONTADO! ({current_batch_count}/{BATCH_SIZE})")

    # Lote concluído
    print(f"[{LINE_ID}] LOTE CONCLUÍDO: {BATCH_SIZE} unidades de '{PRODUCT_ID}' produzidas.")
    publish_line_status(client, current_batch_count, "Lote Concluído. Aguardando...")
    # Notifica o sistema que um novo lote de produtos acabados está disponível
    print(f"[{LINE_ID}] Notificando conclusão do lote ao centro de vendas.")
    client.publish("factory2/order_completed", f"{PRODUCT_ID}:{BATCH_SIZE}")

client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
client.loop_start()

while True:
    if start_new_batch:
        run_production_batch(client)
        start_new_batch = False # Reseta a flag para esperar o próximo dia
    else:
        # Aguardando o sinal para começar um novo dia
        time.sleep(1)
