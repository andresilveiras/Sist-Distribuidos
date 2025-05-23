import zmq
import threading
import time
import sys

'''
Função: receive_messages
Recebe as mensagens de texto do tópico "Chat_Texto"
'''

def receive_messages(context, listen_port):
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://0.0.0.0:{listen_port}")
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "Chat_Texto")

    while True:
        msg = sub_socket.recv_string()
        print(msg)

'''
Função: send_messages
Envia as mensagens de texto para todos os peers inscritos no tópico "Chat_Texto"
'''

def send_messages(context, identity, peer_endpoints):
    pub_socket = context.socket(zmq.PUB)

    for endpoint in peer_endpoints:
        pub_socket.connect(f"tcp://{endpoint}")

    time.sleep(1)
    print(f"Olá {identity}!\nDigite uma mensagem para conversar!")

    while True:
        msg = input()
        topic = "Chat_Texto"
        mensagem = f"{topic} {identity}: {msg}"
        pub_socket.send_string(mensagem)
        time.sleep(0.5)


# ========== PARÂMETROS ==========

# Execução esperada:
# python3 chat.py <Nome> <PortaLocal> <Peer1[:Porta]> [Peer2[:Porta]] ...


if len(sys.argv) < 3:
    print("Uso: python3 chat.py <Nome> <PortaLocal> <Peer1[:Porta]> [Peer2[:Porta]] ...")
    sys.exit(1)

identity = sys.argv[1]
listen_port = int(sys.argv[2])
peer_args = sys.argv[3:]

peer_endpoints = []

for arg in peer_args:
    if ':' in arg:
        ip, port = arg.split(':')
    else:
        ip, port = '127.0.0.1', arg
    peer_endpoints.append(f"{ip}:{port}")

context = zmq.Context()

# Iniciar threads para recepção de mensagens
threading.Thread(target=receive_messages, args=(context, listen_port), daemon=True).start()

# Iniciar threads de envio de mensagens 
send_messages(context, identity, peer_endpoints)
