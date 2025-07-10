import time
from shared.mqtt_client import get_client

DELIVERY_TIME_SECONDS = 15 # Simula 15 segundos para a entrega das peças

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[SUPPLIER] Falha ao conectar: {reason_code}")
    else:
        # O fornecedor agora se inscreve no tópico de pedidos de reabastecimento
        print("[SUPPLIER] Conectado ao broker MQTT. Aguardando ordens de reabastecimento.")
        client.subscribe("estoque/reabastecer")

def on_message(client, userdata, msg):
    """
    Processa ordens de reabastecimento recebidas do almoxarifado.
    """
    payload = msg.payload.decode('utf-8')
    print(f"[SUPPLIER] Ordem de reabastecimento recebida: {msg.topic} -> '{payload}'")
    
    try:
        part_name, quantity_str = payload.split(':')
        quantity = int(quantity_str.strip())

        print(f"[SUPPLIER] Preparando envio de {quantity} unidades de '{part_name}'. Tempo de entrega: {DELIVERY_TIME_SECONDS}s.")
        time.sleep(DELIVERY_TIME_SECONDS)

        print(f"[SUPPLIER] Enviando {quantity} unidades de '{part_name}' para o almoxarifado.")
        # Publica no tópico de check-in para que o almoxarifado receba as peças
        client.publish("estoque/check_in", f"{part_name}:{quantity}")

    except (ValueError, IndexError) as e:
        print(f"[SUPPLIER] ERRO: Não foi possível processar a ordem '{payload}': {e}")

client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
client.loop_forever() # O fornecedor agora fica em loop, apenas esperando por mensagens
