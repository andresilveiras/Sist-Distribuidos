import time
import os
import sys
from shared.mqtt_client import get_client
from shared.products import BOM
import threading

# --- Configurações da Linha ---
LINE_ID = os.getenv("LINE_ID")

if not LINE_ID:
    print(f"[LINE] ERRO: Variável de ambiente LINE_ID não definida.")
    sys.exit(1)

# --- Estado da Linha ---
production_halted = False
is_busy = False # Flag para indicar se a linha está processando uma ordem

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[{LINE_ID}] Falha ao conectar: {reason_code}")
    else:
        print(f"[{LINE_ID}] Conectado ao broker. Aguardando ordens de produção.")
        # Inscrição Compartilhada: Apenas uma linha do grupo 'factory2_workers' receberá a mensagem.
        client.subscribe("$share/factory2_workers/factory2/production_order")
        client.subscribe("estoque/status")
        publish_line_status(client, None, 0, 0, "Ociosa")

"""
Lida com mensagens MQTT recebidas, delegando para a função apropriada.
"""
def on_message(client, userdata, msg):
    if msg.topic == "estoque/status":
        handle_stock_status(msg)
    elif msg.topic == "factory2/production_order":
        handle_production_order(client, msg)

"""
Publica o estado atual da linha para o dashboard.
"""
def publish_line_status(client, product_id, completed, total, status_text):
    if not is_busy: # Se não está ocupada, envia um status padrão
        payload = f"N/A:0:0:{status_text}"
    else:
        payload = f"{product_id}:{completed}:{total}:{status_text}"
    client.publish(f"dashboard/lines/{LINE_ID}", payload, retain=True)

"""
Processa mensagens de status do almoxarifado.
"""
def handle_stock_status(msg):
    global production_halted
    try:
        part_name, status = msg.payload.decode('utf-8').split(':')
        if status == "OUT_OF_STOCK" and not production_halted:
            print(f"[{LINE_ID}] AVISO: Estoque de '{part_name}' insuficiente. Produção parada.")
            production_halted = True
        elif status == "STOCK_OK" and production_halted:
            print(f"[{LINE_ID}] INFO: Estoque normalizado. Retomando produção.")
            production_halted = False
    except (ValueError, IndexError):
        pass # Ignora mensagens mal formatadas

"""
Recebe uma ordem de produção e a inicia em uma nova thread.
"""
def handle_production_order(client, msg):
    global is_busy
    if is_busy:
        return # Se a linha já está ocupada, ignora a nova ordem. Outra linha ociosa pegará.

    # Inicia a produção em uma nova thread para não bloquear o loop MQTT
    production_thread = threading.Thread(target=run_production_process, args=(client, msg.payload))
    production_thread.daemon = True
    production_thread.start()

"""
O processo completo de uma ordem de produção, executado em uma thread.
"""
def run_production_process(client, payload):
    global production_halted, is_busy
    is_busy = True
    try:
        payload_str = payload.decode('utf-8')
        print(f"[{LINE_ID}] Ordem de produção recebida: {payload_str}")
        product_id, quantity_str = payload_str.split(':')
        quantity = int(quantity_str)

        if product_id not in BOM:
            print(f"[{LINE_ID}] ERRO: Produto '{product_id}' desconhecido. Abortando ordem.")
            publish_line_status(client, product_id, 0, quantity, "Erro: Produto inválido")
        else:
            run_blocking_production(client, product_id, quantity)

    except (ValueError, IndexError) as e:
        print(f"[{LINE_ID}] ERRO: Ordem de produção mal formatada '{payload.decode('utf-8')}': {e}")
    finally:
        # Garante que o estado da linha seja resetado ao final do processo
        is_busy = False
        production_halted = False
        print(f"[{LINE_ID}] Linha ociosa. Aguardando novas ordens.")
        publish_line_status(client, None, 0, 0, "Ociosa")

"""
Executa a lógica de produção bloqueante para uma ordem específica.
"""
def run_blocking_production(client, product_id, total_quantity):
    global production_halted
    units_produced = 0
    
    while units_produced < total_quantity:
        parts_needed = set(BOM[product_id])
        publish_line_status(client, product_id, units_produced, total_quantity, "Produzindo")

        while parts_needed:
            if production_halted:
                part_faltando = next(iter(parts_needed))
                publish_line_status(client, product_id, units_produced, total_quantity, f"Parada - Falta {part_faltando}")
                time.sleep(5)
                continue

            part_to_request = parts_needed.pop()
            client.publish("estoque/check_out", f"{part_to_request}:1")
            time.sleep(0.1)

        units_produced += 1
        print(f"[{LINE_ID}] Unidade de '{product_id}' montada! ({units_produced}/{total_quantity})")
        client.publish("production/batch_completed", f"{product_id}:1")

    print(f"[{LINE_ID}] ORDEM CONCLUÍDA: {total_quantity} unidades de '{product_id}' produzidas.")
    publish_line_status(client, product_id, units_produced, total_quantity, "Ordem Concluída")
    # A linha abaixo foi comentada pq antes postava so quando terminava todo o lote, agora publica produto a produto
    #client.publish("production/batch_completed", f"{product_id}:{total_quantity}")
    time.sleep(5) # Simula um tempo de resfriamento/limpeza

if __name__ == "__main__":
    client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
    client.loop_forever()