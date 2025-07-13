import time
import random
from shared.mqtt_client import get_client
from shared.products import BOM

# --- Configurações do Centro de Vendas ---
SIMULATION_DAY_DURATION_SECONDS = 20  # A cada 20 segundos, um "novo dia" de vendas ocorre
PRODUCT_IDS = list(BOM.keys())

# Estoque inicial de produtos acabados e o nível alvo que queremos manter.
finished_goods_inventory = {
    product_id: {
        "current_stock": 50,
        "target_stock": 50,
        "total_sold": 0
    } for product_id in PRODUCT_IDS
}

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[SALES_CENTER] Falha ao conectar ao MQTT: {reason_code}")
        return
    print("[SALES_CENTER] Conectado ao Broker MQTT.")

def get_product_status(stock_info):
    """Calcula o status do estoque de um produto acabado (VERDE, AMARELO, VERMELHO)."""
    if stock_info["target_stock"] == 0: return "VERDE"
    percentage = (stock_info["current_stock"] / stock_info["target_stock"]) * 100
    if percentage <= 30: return "VERMELHO"
    if percentage < 75: return "AMARELO"
    return "VERDE"

def publish_stock_update(client, product_id, stock_info):
    """Publica o estado atualizado de um produto para o dashboard."""
    status = get_product_status(stock_info)
    payload = (f"{stock_info['current_stock']}:{stock_info['target_stock']}:"
               f"{stock_info['total_sold']}:{status}")
    client.publish(f"dashboard/finished_goods/{product_id}", payload)

def simulate_daily_sales_and_production_orders(client):
    """
    Simula um dia de vendas, atualiza o estoque e gera ordens de produção se necessário.
    """
    print("\n--- [SALES_CENTER] Novo dia de simulação ---")

    # 1. Simular vendas para produtos aleatórios
    num_sales = random.randint(1, 3)
    for _ in range(num_sales):
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

    # 2. Verificar necessidade de reabastecimento e emitir ordens de produção
    print("[SALES_CENTER] Verificando necessidade de produção...")
    for product_id, stock_info in finished_goods_inventory.items():
        if stock_info["current_stock"] < stock_info["target_stock"]:
            quantity_to_produce = stock_info["target_stock"] - stock_info["current_stock"]
            
            print(f"[SALES_CENTER] Estoque de '{product_id}' baixo! Gerando ordem de produção para {quantity_to_produce} unidades.")
            
            # Publica a ordem de produção para a Fábrica 2
            client.publish("factory2/production_order", f"{product_id}:{quantity_to_produce}")
            
            # Atualiza o estoque para refletir que a produção foi "encomendada"
            stock_info["current_stock"] += quantity_to_produce
            # Publica a atualização para o dashboard
            publish_stock_update(client, product_id, stock_info)

if __name__ == "__main__":
    client = get_client(on_connect_callback=on_connect)
    client.loop_start() # Inicia o loop em uma thread separada

    # Publica o estado inicial de todos os produtos para o dashboard
    print("[SALES_CENTER] Publicando estado inicial do estoque de produtos acabados.")
    for product_id, stock_info in finished_goods_inventory.items():
        publish_stock_update(client, product_id, stock_info)

    while True:
        simulate_daily_sales_and_production_orders(client)
        time.sleep(SIMULATION_DAY_DURATION_SECONDS)