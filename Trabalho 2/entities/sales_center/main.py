import time
import random
import threading
from datetime import datetime
from shared.mqtt_client import get_client
from shared.products import BOM

# --- Configurações do Centro de Vendas ---
SIMULATION_DAY_DURATION_SECONDS = 600  # A cada 10 minutos, um "novo dia" de vendas ocorre
SALE_EVENT_INTERVAL_SECONDS = 10  # Um novo evento de venda ocorre a cada 10 segundos
PRODUCT_IDS = list(BOM.keys())

# Estoque inicial de produtos acabados e o nível alvo que queremos manter.
finished_goods_inventory = {
    product_id: {
        # --- Escolha o cenário de simulação ---
        # Opção 1: Simulação de Estado Estacionário (Recomendado para testar a resiliência)
        "current_stock": 60,
        # Opção 2: Simulação de Partida a Frio (Bom para ver o sistema inicializar)
        # "current_stock": 0,
        "target_stock": 100,
        "total_sold": 0
    } for product_id in PRODUCT_IDS
}

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[SALES_CENTER] Falha ao conectar ao MQTT: {reason_code}")
        return
    print("[SALES_CENTER] Conectado ao Broker MQTT.")
    # Inscreve-se no tópico para saber quando um lote de produção foi concluído
    client.subscribe("production/batch_completed")

    # Publica o estado inicial de todos os produtos para o dashboard APÓS a conexão
    # Isso garante que as mensagens não sejam perdidas.
    print("[SALES_CENTER] Publicando estado inicial do estoque de produtos acabados.")
    for product_id, stock_info in finished_goods_inventory.items():
        publish_stock_update(client, product_id, stock_info)

"""
Processa mensagens de lotes de produção concluídos.
"""
def on_message(client, userdata, msg):
    if msg.topic == "production/batch_completed":
        payload = msg.payload.decode('utf-8')
        try:
            product_id, quantity_str = payload.split(':')
            quantity = int(quantity_str)
            if product_id in finished_goods_inventory:
                #print(f"[SALES_CENTER] Recebido lote de {quantity} unidades de '{product_id}' da produção.")
                finished_goods_inventory[product_id]["current_stock"] += quantity
                publish_stock_update(client, product_id, finished_goods_inventory[product_id])
        except (ValueError, IndexError) as e:
            print(f"[SALES_CENTER] ERRO: Mensagem de lote concluído mal formatada: '{payload}': {e}")

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
    while True:
        print("\n--- [SALES_CENTER] Anunciando novo dia de produção para as fábricas. ---")
        client.publish("simulation/new_day", f"start_day:{datetime.now().isoformat()}")
        time.sleep(SIMULATION_DAY_DURATION_SECONDS)

"""
Simula um único evento de venda, que pode conter pedidos para múltiplos produtos, utilizando um lock para garantir acesso exclusivo ao cliente MQTT.
"""
def simulate_sale_event(client, lock):
    while True:
        print(f"\n--- [SALES_CENTER] Evento de venda: {datetime.now().isoformat()} ---")

        # 1. Simular um pedido de cliente com 1 a 5 tipos de produtos diferentes
        num_products_in_order = random.randint(1, 5)
        for _ in range(num_products_in_order):
            product_sold = random.choice(PRODUCT_IDS)
            quantity_sold = random.randint(5, 25)
            
            stock = finished_goods_inventory[product_sold]
            
            print(f"[SALES_CENTER] Pedido de cliente: {quantity_sold} unidades de '{product_sold}'.")
            
            # Vende o que for possível
            actual_sold = min(quantity_sold, stock["current_stock"])
            stock["current_stock"] -= actual_sold
            stock["total_sold"] += actual_sold
            print(f"[SALES_CENTER] Venda efetuada. Estoque de '{product_sold}' agora é: {stock['current_stock']}")
            # Publica a atualização para o dashboard
            publish_stock_update(client, product_sold, stock)    
            time.sleep(SALE_EVENT_INTERVAL_SECONDS)

"""
Verifica a necessidade de produção e emite ordens para a Fábrica 2.
"""
def check_and_request_production(client):
    #print("[SALES_CENTER] Verificando necessidade de produção...")
    for product_id, stock_info in finished_goods_inventory.items():
        # A Fábrica 2 (puxada) deve ser acionada quando o estoque está AMARELO ou VERMELHO.
        # A quantidade a produzir é o que falta para atingir o estoque alvo.
        status = get_product_status(stock_info)
        if status == "AMARELO" or status == "VERMELHO":
            quantity_to_produce = stock_info["target_stock"] - stock_info["current_stock"]
            if quantity_to_produce > 0:
                print(f"[SALES_CENTER] Estoque de '{product_id}' baixo! Gerando ordem de produção para {quantity_to_produce} unidades.")
                # Publica a ordem de produção para a Fábrica 2
                client.publish("factory2/production_order", f"{product_id}:{quantity_to_produce}")

if __name__ == "__main__":
    client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
    client.loop_start() # Inicia o loop em uma thread separada

    while True:
        # Cria um Lock para controlar o acesso ao cliente MQTT
        mqtt_lock = threading.Lock()

        # Inicia as threads para o ciclo diário e eventos de venda
        daily_cycle_thread = threading.Thread(target=simulate_daily_cycle, args=(client, mqtt_lock))
        sale_event_thread = threading.Thread(target=simulate_sale_event, args=(client, mqtt_lock))

        daily_cycle_thread.daemon = True  # Permite que o programa termine mesmo com a thread rodando
        sale_event_thread.daemon = True

        daily_cycle_thread.start()
        sale_event_thread.start()

        # Verificamos a necessidade de produção após cada ciclo de vendas (agora rodando independentemente)
        with mqtt_lock:  # Garante acesso exclusivo ao cliente MQTT
            check_and_request_production(client)