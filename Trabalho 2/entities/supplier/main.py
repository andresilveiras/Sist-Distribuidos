import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc):
    print("[SUPPLIER] Conectado ao broker MQTT")

client = mqtt.Client()
client.on_connect = on_connect
client.connect("broker", 1883, 60)
client.loop_start()

while True:
    print("[SUPPLIER] Fornecendo peças para almoxarifado...")
    time.sleep(10)
