from shared.buffer import Buffer
from shared.mqtt_client import get_client

buffer = Buffer("Parte A", 100, 60, 30)
print(f"[WAREHOUSE] Almoxarifado iniciado para '{buffer.part_name}'. Status inicial: {buffer}")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[WAREHOUSE] Falha ao conectar: {reason_code}")
    else:
        # Inscreve-se no tópico de check-out quando a conexão é estabelecida
        print("[WAREHOUSE] Conectado ao broker MQTT. Inscrevendo-se em 'estoque/check_out'")
        client.subscribe("estoque/check_out")

def on_message(client, userdata, msg):
    """
    Processa mensagens de check-out do estoque.
    """
    payload = msg.payload.decode('utf-8')
    print(f"[WAREHOUSE] Mensagem recebida: {msg.topic} -> '{payload}'")
    
    try:
        part_name, quantity_str = payload.split(':')
        quantity = int(quantity_str.strip())

        # Assume que o buffer é para a "Parte A" conforme inicializado
        if part_name.strip() == buffer.part_name:
            # O README menciona um método CheckOut, vamos usar check_out por convenção Python
            buffer.check_out(quantity)
            print(f"[WAREHOUSE] Check-out de {quantity} da '{part_name.strip()}' realizado.")
            # O README diz que o buffer deve ser mostrado em tela com seu valor e COR
            print(f"[WAREHOUSE] Novo status do estoque: {buffer}") 
        else:
            print(f"[WAREHOUSE] AVISO: Recebida solicitação para parte não gerenciada: {part_name.strip()}")

    except (ValueError, IndexError) as e:
        print(f"[WAREHOUSE] ERRO: Não foi possível processar a mensagem '{payload}': {e}")

# Passamos a função de callback para o helper
client = get_client(on_connect_callback=on_connect, on_message_callback=on_message)
client.loop_forever()
