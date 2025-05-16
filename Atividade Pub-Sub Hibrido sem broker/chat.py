import zmq
import threading
import time
import sys

def receive_messages(context, listen_port):
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://*:{listen_port}")
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "Mensagem")

    while True:
        msg = sub_socket.recv_string()
        print(msg)

def send_messages(context, identity, peer_ports):
    pub_socket = context.socket(zmq.PUB)

    # Conectando aos peers
    for port in peer_ports:
        pub_socket.connect(f"tcp://localhost:{port}")

    time.sleep(1)  # Tempo para estabilizar conexões
    print(f"Olá {identity}!\nDigite uma mensagem para conversar!")

    while True:
        msg = input()
        mensagem = f"Mensagem de {identity}: {msg}"
        pub_socket.send_string(mensagem)
        time.sleep(0.5)

# ========== PARÂMETROS ==========

# Execução esperada:
# python3 chat_sem_broker.py Nome 6000 6001 6002
# Onde:
# - Nome é o nome do usuário
# - 6000 é a porta local de escuta
# - 6001, 6002... são portas de outros peers

if len(sys.argv) < 3:
    print("Uso: python3 chat_sem_broker.py <Nome> <PortaLocal> <PortaPeer1> [PortaPeer2] ...")
    sys.exit(1)

identity = sys.argv[1]
listen_port = sys.argv[2]
peer_ports = sys.argv[3:]

context = zmq.Context()

# Thread para receber mensagens
threading.Thread(target=receive_messages, args=(context, listen_port), daemon=True).start()

# Enviar mensagens
send_messages(context, identity, peer_ports)
