import time
from shared.mqtt_client import get_client

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[LINE1] Falha ao conectar: {reason_code}")
    else:
        print("[LINE1] Conectado ao broker MQTT")

client = get_client(on_connect_callback=on_connect)
client.loop_start()

# Uma pequena pausa para garantir que a conexão em background seja estabelecida
time.sleep(1) 

print("[LINE1] Iniciando ciclo de produção.")
while True:
    print("[LINE1] Solicitando parte do almoxarifado...")
    client.publish("estoque/check_out", "Parte A: 5")
    time.sleep(5)
