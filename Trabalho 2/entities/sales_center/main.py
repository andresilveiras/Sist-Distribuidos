import time
import random
import threading
from datetime import datetime
from shared.mqtt_client import get_client
from shared.products import BOM

# --- Configurações do Centro de Vendas ---
SIMULATION_DAY_DURATION_SECONDS = 600  # A cada 10 minutos, um "novo dia" de vendas ocorre
SALE_EVENT_INTERVAL_SECONDS = 15  # Um novo evento de venda ocorre a cada 15 segundos
PRODUCT_IDS = list(BOM.keys())

# Estoque inicial de produtos acabados e o nível alvo que queremos manter.
finished_goods_inventory = {
    product_id: {
        # --- Escolha o cenário de simulação ---
        # Opção 1: Simulação de Estado Estacionário (Recomendado para testar a resiliência)
        "current_stock": 80,
        # Opção 2: Simulação de Partida a Frio (Bom para ver o sistema inicializar)
        # "current_stock": 0,
        "target_stock": 100,
        "total_sold": 0
    } for product_id in PRODUCT_IDS
}

# Dicionario para rastrear ordens de produção pendentes para a Fábrica 2.
pending_orders = {product_id: False for product_id in PRODUCT_IDS}

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[SALES_CENTER] Falha ao conectar ao MQTT: {reason_code}")
        return
    print("[SALES_CENTER] Conectado ao Broker MQTT.")
    client.subscribe("production/batch_completed")      # status que uma linha da fabrica 2 terminou de produzir um lote
    client.subscribe("production/product_completed")    # um novo produto foi produzido (ambas as fabricas)

    # Publica o estado inicial de todos os produtos para o dashboard APÓS a conexão
    # Isso garante que as mensagens não sejam perdidas.
    print("[SALES_CENTER] Publicando estado inicial do estoque de produtos acabados.")
    for product_id, stock_info in finished_goods_inventory.items():
        publish_stock_update(client, product_id, stock_info)

"""
Processa mensagens de lotes de produção concluídos.
"""
def on_message(client, userdata, msg):
    # Recebeu mensagem de produto montado (ambas as fabricas)
    if msg.topic == "production/product_completed":
        payload = msg.payload.decode('utf-8')
        try:
            product_id, quantity_str = payload.split(':')
            quantity = int(quantity_str)
            if product_id in finished_goods_inventory:
                #print(f"[SALES_CENTER] Recebido lote de {quantity} unidades de '{product_id}' da produção.")
                finished_goods_inventory[product_id]["current_stock"] += quantity
                publish_stock_update(client, product_id, finished_goods_inventory[product_id])
        except (ValueError, IndexError) as e:
            print(f"[SALES_CENTER] ERRO: Mensagem mal formatada: '{payload}': {e}")

    # Recebeu mensagem de lote concluido (apenas fabrica 2 - libera a linha p/ proximos pedidos)
    if msg.topic == "production/batch_completed": 
        payload = msg.payload.decode('utf-8')
        try:
            product_id, quantity_str = payload.split(':')
            pending_orders[product_id] = False
            print(f"Ordens de produção p/ fábrica 2: {pending_orders}")
        except (ValueError, IndexError) as e:
            print(f"[SALES_CENTER] ERRO: Mensagem mal formatada: '{payload}': {e}")

"""
Calcula o status do estoque de um produto acabado (VERDE, AMARELO, VERMELHO).
"""
def get_product_status(stock_info):
    if stock_info["target_stock"] == 0: return "VERDE"
    percentage = (stock_info["current_stock"] / stock_info["target_stock"]) * 100
    if percentage <= 25: return "VERMELHO"
    if percentage < 50: return "AMARELO"
    return "VERDE"

"""
Publica o estado atualizado de um produto para o dashboard.
"""
def publish_stock_update(client, product_id, stock_info):
    status = get_product_status(stock_info)
    payload = (f"{stock_info['current_stock']}:{stock_info['target_stock']}:"
               f"{stock_info['total_sold']}:{status}")
    client.publish(f"dashboard/finished_goods/{product_id}", payload, retain=True)

"""
Simula o ciclo diário, publicando o sinal de "novo dia" para a Fábrica 1., utilizando um lock para garantir acesso exclusivo ao cliente MQTT.
"""
def simulate_daily_cycle(client, lock):
    with lock:
        client.publish("simulation/new_day", f"start_day:{datetime.now().isoformat()}")
        print(f"[SALES_CENTER] ---- NOVO DIA INICIADO ----")

"""
Simula um único evento de venda, que pode conter pedidos para múltiplos produtos, utilizando um lock para garantir acesso exclusivo ao cliente MQTT.
"""
def simulate_sale_event(client, lock):
    with lock:
        # Simula um pedido de cliente com 1 a 5 tipos de produtos diferentes
        print(f"[SALES_CENTER] ---- VENDA INICIADA ----")
        num_products_in_order = random.randint(1, 5)
        for _ in range(num_products_in_order):
            product_sold = random.choice(PRODUCT_IDS)
            quantity_sold = random.randint(1, 10)
            stock = finished_goods_inventory[product_sold]
            print(f"[SALES_CENTER] Pedido de cliente: {quantity_sold} unidades de '{product_sold}'.")
            # Vende o que for possível
            actual_sold = min(quantity_sold, stock["current_stock"])
            stock["current_stock"] -= actual_sold
            stock["total_sold"] += actual_sold
            print(f"[SALES_CENTER] Venda efetuada. Estoque de '{product_sold}' agora é: {stock['current_stock']}")
            # Publica a atualização para o dashboard
            publish_stock_update(client, product_sold, stock)
        print(f"[SALES_CENTER] ------------------------")

"""
Verifica a necessidade de produção e emite ordens para a Fábrica 2.
"""
def check_and_request_production(client, lock):
    with lock:
        for product_id, stock_info in finished_goods_inventory.items():
            status = get_product_status(stock_info)
            
            # No Status AMARELO, verifica se já foi feito um pedido de produção p/ fábrica 2 e faz pedido somente se nao foi feito outro antes

            if(status == "AMARELO" and not pending_orders[product_id]):
                quantity_to_produce = 25
                print(f"[SALES_CENTER] Estoque de '{product_id}' baixo! Gerando ordem de produção para {quantity_to_produce} unidades.")
                # Publica a ordem de produção para a Fábrica 2
                client.publish("factory2/production_order", f"{product_id}:{quantity_to_produce}")
                pending_orders[product_id] = True
                print(f"Ordens de produção p/ fábrica 2: {pending_orders}")

            # No Status VERMELHO, faz pedido de produção p/ fábrica 2 sem restrições
            
            if status == "VERMELHO":
                quantity_to_produce = 50
                print(f"[SALES_CENTER] ESTOQUE DE '{product_id}' EM NÍVEL CRÍTICO! Gerando ordem de produção para {quantity_to_produce} unidades.")
                # Publica a ordem de produção para a Fábrica 2
                client.publish("factory2/production_order", f"{product_id}:{quantity_to_produce}")
                

def run_daily_cycle(client, lock):
    while True:
        simulate_daily_cycle(client, lock)
        time.sleep(SIMULATION_DAY_DURATION_SECONDS)


def run_sale_event(client, lock):
    while True:
        simulate_sale_event(client, lock)
        check_and_request_production(client, lock)
        time.sleep(SALE_EVENT_INTERVAL_SECONDS)

if __name__ == "__main__":
    client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
    client.loop_start() # Inicia o loop em uma thread separada
    mqtt_lock = threading.Lock()
    threading.Thread(target=run_daily_cycle, args=(client, mqtt_lock), daemon=True).start()
    threading.Thread(target=run_sale_event, args=(client, mqtt_lock), daemon=True).start()
    while True: time.sleep(1) # Mantém o programa principal rodando