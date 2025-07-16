import time
from shared.mqtt_client import get_client
from shared.products import PART_DELIVERY_TIMES
from concurrent.futures import ThreadPoolExecutor

# --- Configurações do Fornecedor ---
MAX_CONCURRENT_ORDERS = 5 # Define o número máximo de pedidos processados simultaneamente

# Cria um "pool de threads" com um número fixo de workers.
# Isso evita a criação ilimitada de threads, gerenciando os recursos do sistema.
executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_ORDERS)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[SUPPLIER] Falha ao conectar: {reason_code}")
    else:
        # O fornecedor agora se inscreve no tópico de pedidos de reabastecimento
        print("[SUPPLIER] Conectado ao broker MQTT. Aguardando ordens de reabastecimento.")
        client.subscribe("estoque/reabastecer")

"""
Função que executa em uma thread do pool para processar um único pedido.
"""
def process_order(client, part_name, quantity):
    try:
        delivery_time = PART_DELIVERY_TIMES[part_name]
        print(f"[SUPPLIER] INICIANDO processamento de '{part_name}'. Tempo de entrega: {delivery_time}s.")
        time.sleep(delivery_time)

        print(f"[SUPPLIER] FINALIZADO o processamento de '{part_name}'. Enviando para o almoxarifado.")
        client.publish("estoque/check_in", f"{part_name}:{quantity}")
    except KeyError as e:
        print(f"[SUPPLIER] ERRO: Peça desconhecida no dicionário de entregas: {e}")
    except Exception as e:
        print(f"[SUPPLIER] ERRO inesperado ao processar pedido para '{part_name}': {e}")

"""
Recebe uma ordem de reabastecimento e a submete ao pool de threads para processamento.
"""
def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    print(f"[SUPPLIER] Ordem recebida: '{payload}'. Adicionando à fila de processamento.")
    
    try:
        part_name, quantity_str = payload.split(':')
        part_name = part_name.strip()
        quantity = int(quantity_str.strip())

        # Submete a tarefa para o pool de threads.
        # O executor vai agendar a execução da função 'process_order' quando uma thread estiver livre.
        executor.submit(process_order, client, part_name, quantity)
    except (ValueError, IndexError) as e:
        print(f"[SUPPLIER] ERRO: Não foi possível processar a ordem '{payload}': {e}")

if __name__ == "__main__":
    client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
    client.loop_forever() # O fornecedor agora fica em loop, apenas esperando por mensagens
