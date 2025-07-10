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

production_halted = False # Flag para parar a produção se faltar qualquer peça
parts_needed_for_current_unit = set(BOM[PRODUCT_ID])
current_batch_count = 0

def publish_line_status(client, status_text):
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
        publish_line_status(client, "Iniciando")

def on_message(client, userdata, msg):
    """Processa mensagens de status do almoxarifado."""
    global production_halted, parts_needed_for_current_unit
    payload = msg.payload.decode('utf-8')
    
    try:
        part_name, status = payload.split(':')
        part_name = part_name.strip()
        status = status.strip()
        
        if status == "CHECKOUT_SUCCESS" and part_name in parts_needed_for_current_unit:
            #print(f"[LINE {LINE_ID}] Peça '{part_name}' recebida do almoxarifado.")
            parts_needed_for_current_unit.remove(part_name)
        
        elif status == "OUT_OF_STOCK" and not production_halted:
            print(f"[LINE {LINE_ID}] AVISO: Estoque de '{part_name}' insuficiente. Produção parada.")
            publish_line_status(client, f"Parada - Falta {part_name}")
            production_halted = True

        elif status == "STOCK_OK" and production_halted:
            print(f"[LINE {LINE_ID}] INFO: Estoque normalizado. Retomando produção.")
            publish_line_status(client, "Produzindo")
            production_halted = False

    except (ValueError, IndexError):
        # Ignora mensagens mal formatadas
        pass

client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
client.loop_start()
time.sleep(1) 

while current_batch_count < BATCH_SIZE:
    if not parts_needed_for_current_unit:
        current_batch_count += 1
        print(f"[LINE {LINE_ID}] PRODUTO {PRODUCT_ID} MONTADO! ({current_batch_count}/{BATCH_SIZE})")
        publish_line_status(client, "Produzindo")
        if current_batch_count < BATCH_SIZE:
            parts_needed_for_current_unit = set(BOM[PRODUCT_ID])
        else:
            break # Lote finalizado

    if production_halted:
        print(f"[LINE {LINE_ID}] Produção parada, aguardando peças.")
        time.sleep(5)
    else:
        # Solicita a próxima peça necessária
        part_to_request = next(iter(parts_needed_for_current_unit))
        #print(f"[LINE {LINE_ID}] Solicitando peça '{part_to_request}' para o produto {PRODUCT_ID}.")
        client.publish("estoque/check_out", f"{part_to_request}:1")
        time.sleep(0.5) # Pequena pausa para não sobrecarregar o broker

publish_line_status(client, "Finalizada")
print(f"[LINE {LINE_ID}] Lote de {BATCH_SIZE} unidades de {PRODUCT_ID} finalizado.")
