import paho.mqtt.client as mqtt
from typing import Callable

BROKER_ADDRESS = "broker"
BROKER_PORT = 1883

def get_client(on_connect_callback: Callable = None, on_message_callback: Callable = None) -> mqtt.Client:
    """
    Initializes the MQTT client, sets the modern callback API to fix DeprecationWarning,
    and assigns optional on_connect and on_message callbacks.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if on_connect_callback:
        client.on_connect = on_connect_callback
    if on_message_callback:
        client.on_message = on_message_callback
    
    client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
    return client