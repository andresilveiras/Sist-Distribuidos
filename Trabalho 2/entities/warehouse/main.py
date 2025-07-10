from shared.buffer import Buffer
from shared.mqtt_client import get_client

buffer = Buffer("Parte A", 100, 60, 30)
# Flag para evitar múltiplos pedidos de reabastecimento enquanto o estoque está baixo
restock_ordered = False

print(f"[WAREHOUSE] Almoxarifado iniciado para '{buffer.part_name}'. Status inicial: {buffer}")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[WAREHOUSE] Falha ao conectar: {reason_code}")
    else:
        # Inscreve-se no tópico de check-out quando a conexão é estabelecida
        print("[WAREHOUSE] Conectado ao broker MQTT. Inscrevendo-se nos tópicos.")
        client.subscribe("estoque/check_out")
        client.subscribe("estoque/check_in")

def on_message(client, userdata, msg):
    """
    Processa mensagens de check-out e check-in do estoque.
    """
    global restock_ordered
    payload = msg.payload.decode('utf-8')
    print(f"[WAREHOUSE] Mensagem recebida: {msg.topic} -> '{payload}'")
    
    try:
        part_name, quantity_str = payload.split(':')
        quantity = int(quantity_str.strip())
        
        # Ignora mensagens para outras peças
        if part_name.strip() != buffer.part_name:
            print(f"[WAREHOUSE] AVISO: Recebida solicitação para parte não gerenciada: {part_name.strip()}")
            return
        
        # Lógica de Tópicos
        if msg.topic == "estoque/check_out":
            if buffer.check_out(quantity):
                print(f"[WAREHOUSE] Check-out de {quantity} da '{part_name.strip()}' realizado.")
            else:
                print(f"[WAREHOUSE] FALHA NO CHECK-OUT: Estoque insuficiente para '{part_name.strip()}'.")
            
            # Mostra o status do estoque
            print(f"[WAREHOUSE] Novo status do estoque: {buffer}") 

            # Verifica se precisa reabastecer
            if buffer.status == "VERMELHO" and not restock_ordered:
                print(f"[WAREHOUSE] NÍVEL CRÍTICO ATINGIDO. Solicitando reabastecimento ao fornecedor.")
                # Pede um lote fixo para reabastecer (ex: 70 unidades)
                restock_batch_size = 70 
                client.publish("estoque/reabastecer", f"{buffer.part_name}:{restock_batch_size}")
                restock_ordered = True

        elif msg.topic == "estoque/check_in":
            buffer.check_in(quantity)
            print(f"[WAREHOUSE] Check-in de {quantity} da '{part_name.strip()}' realizado.")
            print(f"[WAREHOUSE] Novo status do estoque: {buffer}")
            
            # Se o estoque saiu do vermelho, podemos permitir um novo pedido no futuro
            if buffer.status != "VERMELHO":
                restock_ordered = False
                print("[WAREHOUSE] Nível de estoque normalizado.")

    except (ValueError, IndexError) as e:
        print(f"[WAREHOUSE] ERRO: Não foi possível processar a mensagem '{payload}': {e}")

# Passamos a função de callback para o helper
client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
client.loop_forever()
