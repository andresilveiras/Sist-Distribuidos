import time
from shared.mqtt_client import get_client

def on_connect(client, userdata, flags, rc):
    print("[SUPPLIER] Conectado ao broker MQTT")

# Passamos a função de callback para nosso novo helper
client = get_client(on_connect_callback=on_connect)
client.loop_start()

while True:
    print("[SUPPLIER] Fornecendo peças para almoxarifado...")
    time.sleep(10)
