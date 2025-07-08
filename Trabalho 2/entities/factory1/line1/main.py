import time
from shared.mqtt_client import get_client

client = get_client()
client.loop_start()

while True:
    print("[LINE1] Solicitando parte do almoxarifado...")
    client.publish("estoque/check_out", "Parte A: 5")
    time.sleep(5)
