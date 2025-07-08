from shared.buffer import Buffer
from shared.mqtt_client import get_client

buffer = Buffer("Parte A", 100, 60, 30)

def on_message(client, userdata, msg):
    print(f"[WAREHOUSE] Mensagem recebida: {msg.topic} -> {msg.payload}")

# Passamos a função de callback para nosso novo helper
client = get_client(on_message_callback=on_message)
client.subscribe("estoque/check_out")
client.loop_forever()
