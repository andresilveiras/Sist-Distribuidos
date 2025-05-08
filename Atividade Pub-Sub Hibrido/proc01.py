import zmq
import threading
import time
import sys

def receive_messages():
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://localhost:5560")  # Broker's XPUB
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "Mensagem")

    while True:
        msg = sub_socket.recv_string()
        print(msg)

def send_messages(identity):
    pub_socket = context.socket(zmq.PUB)
    pub_socket.connect("tcp://localhost:5559")  # Broker's XSUB

    time.sleep(1)  # Aguarda conexão
    print(f"Olá {identity}!\nDigite uma mensagem para conversar!")

    while True:
        msg = input()
        mensagem = f"Mensagem de {identity}: {msg}"
        pub_socket.send_string(mensagem)
        #print(f"[ENVIADO] {mensagem}")
        time.sleep(1)

context = zmq.Context()
identity = sys.argv[1] if len(sys.argv) > 1 else "Anon"

# Thread para receber
threading.Thread(target=receive_messages, daemon=True).start()

# Função principal envia
send_messages(identity)
