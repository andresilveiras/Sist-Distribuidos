import paho.mqtt.client as mqtt
from shared.buffer import Buffer

buffer = Buffer("Parte A", 100, 60, 30)

def on_message(client, userdata, msg):
    print(f"[WAREHOUSE] Mensagem recebida: {msg.topic} -> {msg.payload}")

client = mqtt.Client()
client.on_message = on_message
client.connect("broker", 1883, 60)
client.subscribe("estoque/check_out")
client.loop_forever()
