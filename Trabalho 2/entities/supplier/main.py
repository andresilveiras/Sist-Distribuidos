import time
from shared.mqtt_client import get_client

# A assinatura da função foi atualizada para a API v2 do Paho-MQTT.
# O parâmetro 'rc' foi substituído por 'reason_code' e 'properties' foi adicionado.
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[SUPPLIER] Falha ao conectar: {reason_code}")
    else:
        print("[SUPPLIER] Conectado ao broker MQTT")

# Passamos a função de callback para nosso novo helper
client = get_client(on_connect_callback=on_connect)
client.loop_start()

while True:
    print("[SUPPLIER] Fornecendo peças para almoxarifado...")
    time.sleep(10)
