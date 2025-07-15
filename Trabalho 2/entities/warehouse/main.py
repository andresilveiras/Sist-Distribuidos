from shared.buffer import Buffer
from shared.mqtt_client import get_client
from shared.products import ALL_PARTS, PART_BATCH_SIZES

# --- Configurações do Almoxarifado ---
# Cria um inventário com um buffer para cada uma das 100 peças.
inventory = {
    part_name: Buffer(part_name, max_capacity=100, yellow_level=50, red_level=25)
    for part_name in ALL_PARTS
}
# Dicionário para controlar se um pedido de reabastecimento já foi feito para uma peça.
restock_ordered = {part_name: False for part_name in ALL_PARTS}

print(f"[WAREHOUSE] Almoxarifado iniciado, gerenciando {len(inventory)} tipos de peças.")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[WAREHOUSE] Falha ao conectar: {reason_code}")
    else:
        # Inscreve-se no tópico de check-out quando a conexão é estabelecida
        print("[WAREHOUSE] Conectado ao broker MQTT. Inscrevendo-se nos tópicos.")
        client.subscribe("estoque/check_out")
        # O almoxarifado também precisa se inscrever no tópico de check_in para receber peças do fornecedor
        client.subscribe("estoque/check_in")
        client.subscribe("estoque/reabastecer")

def on_message(client, userdata, msg):
    """
    Processa mensagens de check-out e check-in do estoque.
    """
    payload = msg.payload.decode('utf-8')
    #print(f"[WAREHOUSE] Mensagem recebida: {msg.topic} -> '{payload}'")
    
    try:
        part_name, quantity_str = payload.split(':')
        part_name = part_name.strip()
        quantity = int(quantity_str.strip())
        
        # Verifica se a peça existe no inventário
        if part_name not in inventory:
            print(f"[WAREHOUSE] AVISO: Recebida solicitação para peça desconhecida: {part_name}")
            return
        
        buffer = inventory[part_name]

        # Lógica de Tópicos
        if msg.topic == "estoque/check_out":
            if buffer.check_out(quantity):
                #print(f"[WAREHOUSE] Check-out de {quantity} da '{part_name}' realizado.")
                client.publish("estoque/status", f"{part_name}:CHECKOUT_SUCCESS")
            else:
                print(f"[WAREHOUSE] FALHA NO CHECK-OUT: Estoque insuficiente para '{part_name}'.")
                # Informa a linha que o estoque acabou
                client.publish("estoque/status", f"{part_name}:OUT_OF_STOCK")
            
            # Mostra o status do estoque
            #print(f"[WAREHOUSE] Novo status do estoque: {buffer}")
            # Publica a atualização para o dashboard
            client.publish(f"dashboard/inventory/{part_name}", f"{buffer.current_quantity}:{buffer.status}")

            # Verifica se precisa reabastecer
            if ((buffer.status == "AMARELO" or buffer.status == "VERMELHO") and not restock_ordered[part_name]):
                print(f"[WAREHOUSE] NÍVEL CRÍTICO ATINGIDO. Solicitando reabastecimento ao fornecedor.")
                restock_batch_size = PART_BATCH_SIZES[part_name]
                client.publish("estoque/reabastecer", f"{part_name}:{restock_batch_size}")
                restock_ordered[part_name] = True

        elif msg.topic == "estoque/check_in":
            previous_quantity = buffer.current_quantity
            buffer.check_in(quantity)
            #print(f"[WAREHOUSE] Check-in de {quantity} da '{part_name}' realizado.")
            #print(f"[WAREHOUSE] Novo status do estoque: {buffer}")
            # Publica a atualização para o dashboard
            client.publish(f"dashboard/inventory/{part_name}", f"{buffer.current_quantity}:{buffer.status}")
            
            # Se o estoque estava baixo (insuficiente para um pedido) e agora está OK, notifica a linha.
            # Assumimos que a linha precisa de pelo menos 1 unidade para continuar.
            if previous_quantity == 0 and buffer.current_quantity > 0:
                 print(f"[WAREHOUSE] Estoque de '{part_name}' normalizado. Notificando linhas de produção.")
                 client.publish("estoque/status", f"{part_name}:STOCK_OK")

            # Se o estoque saiu do vermelho, podemos permitir um novo pedido no futuro
            if buffer.status != "VERMELHO":
                restock_ordered[part_name] = False

    except (ValueError, IndexError) as e:
        print(f"[WAREHOUSE] ERRO: Não foi possível processar a mensagem '{payload}': {e}")

# Passamos a função de callback para o helper
client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
client.loop_forever()
