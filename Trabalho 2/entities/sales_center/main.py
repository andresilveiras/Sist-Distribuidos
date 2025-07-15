import time
import random
from datetime import datetime
from shared.mqtt_client import get_client
from shared.products import BOM

# --- Configurações do Centro de Vendas ---
SIMULATION_DAY_DURATION_SECONDS = 600  # A cada 10 minutos, um "novo dia" de vendas ocorre
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

def on_message(client, userdata, msg):
    """Processa mensagens de lotes de produção concluídos."""
    if msg.topic == "production/batch_completed":
        payload = msg.payload.decode('utf-8')
        try:
            product_id, quantity_str = payload.split(':')
            quantity = int(quantity_str)
            if product_id in finished_goods_inventory:
                print(f"[SALES_CENTER] Recebido lote de {quantity} unidades de '{product_id}' da produção.")
                finished_goods_inventory[product_id]["current_stock"] += quantity
                publish_stock_update(client, product_id, finished_goods_inventory[product_id])
        except (ValueError, IndexError) as e:
            print(f"[SALES_CENTER] ERRO: Mensagem de lote concluído mal formatada: '{payload}': {e}")

def get_product_status(stock_info):
    """Calcula o status do estoque de um produto acabado (VERDE, AMARELO, VERMELHO)."""
    if stock_info["target_stock"] == 0: return "VERDE"
    percentage = (stock_info["current_stock"] / stock_info["target_stock"]) * 100
    if percentage <= 25: return "VERMELHO"
    if percentage < 50: return "AMARELO"
    return "VERDE"

def publish_stock_update(client, product_id, stock_info):
    """Publica o estado atualizado de um produto para o dashboard."""
    status = get_product_status(stock_info)
    payload = (f"{stock_info['current_stock']}:{stock_info['target_stock']}:"
               f"{stock_info['total_sold']}:{status}")
    client.publish(f"dashboard/finished_goods/{product_id}", payload, retain=True)

def simulate_daily_sales_and_production_orders(client):
    """
    Simula um dia de vendas, atualiza o estoque e gera ordens de produção se necessário.
    """
    # Anuncia o início de um novo dia para todas as entidades que precisam saber
    print("\n--- [SALES_CENTER] Anunciando novo dia de produção para as fábricas. ---")
    client.publish("simulation/new_day", f"start_day:{datetime.now().isoformat()}")

    print("\n--- [SALES_CENTER] Novo dia de simulação ---")

    # 1. Simular vendas para produtos aleatórios, espaçadas ao longo do "dia"
    num_sales = random.randint(2, 10)
    if num_sales > 0:
        # Calcula o intervalo entre as vendas para preencher a duração do dia
        delay_between_sales = SIMULATION_DAY_DURATION_SECONDS / num_sales
    
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
        
        # Aguarda um pouco antes da próxima venda, simulando o passar do tempo
        time.sleep(delay_between_sales)

    # 2. Verificar necessidade de reabastecimento e emitir ordens de produção
    print("[SALES_CENTER] Verificando necessidade de produção...")
    for product_id, stock_info in finished_goods_inventory.items():
        # A Fábrica 2 (puxada) só deve ser acionada em caso de emergência (estoque VERMELHO)
        status = get_product_status(stock_info)
        if status == "AMARELO" or status == "VERMELHO":
            quantity_to_produce = stock_info["target_stock"] - stock_info["current_stock"]
            
            print(f"[SALES_CENTER] Estoque de '{product_id}' baixo! Gerando ordem de produção para {quantity_to_produce} unidades.")
            
            # Publica a ordem de produção para a Fábrica 2
            client.publish("factory2/production_order", f"{product_id}:{quantity_to_produce}")

if __name__ == "__main__":
    client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
    client.loop_start() # Inicia o loop em uma thread separada

    while True:
        simulate_daily_sales_and_production_orders(client)
        # Pequena pausa antes de iniciar o próximo ciclo diário
        time.sleep(1)