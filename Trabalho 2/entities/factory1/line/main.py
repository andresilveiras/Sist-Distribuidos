import time
import os
import sys
from shared.mqtt_client import get_client
from shared.products import BOM
import threading

# --- Configurações da Linha ---
LINE_ID = os.getenv("LINE_ID")
PRODUCT_ID = os.getenv("PRODUCT_ID")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "60"))

if not LINE_ID:
    print(f"[LINE] ERRO: Variável de ambiente LINE_ID não definida.")
    sys.exit(1)
if not PRODUCT_ID or PRODUCT_ID not in BOM:
    print(f"[LINE {LINE_ID}] ERRO: Variável de ambiente PRODUCT_ID inválida ou não definida.")
    sys.exit(1)

# --- Estado da Linha ---
production_halted = False
start_new_batch = True # Flag para controlar o início de um novo lote
is_producing = False # Flag para evitar iniciar um novo lote enquanto um já está em andamento

"""
Publica o estado atual da linha para o dashboard.
"""
def publish_line_status(client, current_batch_count, status_text):
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

"""
Processa mensagens de status do almoxarifado.
"""
def on_message(client, userdata, msg):
    global production_halted, start_new_batch, is_producing
    payload = msg.payload.decode('utf-8')
    
    if msg.topic == "simulation/new_day":
        if not is_producing:
            print(f"[LINE {LINE_ID}] Sinal de 'novo dia' recebido. Preparando para iniciar novo lote.")
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

"""
Executa a lógica de produção para um lote completo.
"""
def run_production_batch(client):
    global production_halted, is_producing
    try:
        current_batch_count = 0
        print(f"[LINE {LINE_ID}] Iniciando novo lote de produção.")
        
        while current_batch_count < BATCH_SIZE:
            parts_needed_for_current_unit = set(BOM[PRODUCT_ID])
            publish_line_status(client, current_batch_count, "Produzindo")

            while parts_needed_for_current_unit:
                if production_halted:
                    part_name_faltando = next(iter(parts_needed_for_current_unit)) # Apenas para exibir
                    publish_line_status(client, current_batch_count, f"Parada - Falta {part_name_faltando}")
                    time.sleep(1)
                    continue

                part_to_request = parts_needed_for_current_unit.pop()
                client.publish("estoque/check_out", f"{part_to_request}:1")
                time.sleep(0.1)

            current_batch_count += 1
            print(f"[LINE {LINE_ID}] PRODUTO {PRODUCT_ID} MONTADO! ({current_batch_count}/{BATCH_SIZE})")
            # Notifica a conclusão de CADA unidade em tempo real.
            client.publish("production/batch_completed", f"{PRODUCT_ID}:1")

        # Lote concluído
        print(f"[{LINE_ID}] LOTE CONCLUÍDO: {BATCH_SIZE} unidades de '{PRODUCT_ID}' produzidas.")
        publish_line_status(client, current_batch_count, "Lote Concluído. Aguardando...")
    finally:
        # Garante que a linha seja marcada como não produzindo, mesmo se ocorrer um erro
        is_producing = False
        print(f"[{LINE_ID}] Linha liberada. Aguardando próximo dia.")

if __name__ == "__main__":

    client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
    client.loop_start()

    while True:
        if start_new_batch and not is_producing:
            is_producing = True
            start_new_batch = False # Reseta a flag para esperar o próximo dia
            thread = threading.Thread(target=run_production_batch, args=(client,))
            thread.daemon = True
            thread.start()
        else:
            # Aguardando o sinal para começar um novo dia
            time.sleep(1)
