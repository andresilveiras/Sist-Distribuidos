import paho.mqtt.client as mqtt
import time

client = mqtt.Client()
client.connect("broker", 1883, 60)
client.loop_start()

while True:
    print("[LINE1] Solicitando parte do almoxarifado...")
    client.publish("estoque/check_out", "Parte A: 5")
    time.sleep(5)
