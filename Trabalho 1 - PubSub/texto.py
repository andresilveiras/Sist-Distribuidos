import time
from prompt_toolkit import prompt
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import print_formatted_text
import zmq

def receive_messages(context, listen_port):
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://0.0.0.0:{listen_port}")
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "Chat_Texto")

    while True:
        topico, mensagem = sub_socket.recv_multipart()
        if topico == b"Chat_Texto":
            print_formatted_text(mensagem.decode())

def send_messages(context, nickname, peer_endpoints):
    pub_socket = context.socket(zmq.PUB)
    for endpoint in peer_endpoints:
        pub_socket.connect(f"tcp://{endpoint}")
    time.sleep(1)
    print(f"Olá {nickname}!\nDigite uma mensagem para conversar!")

    with patch_stdout():
        while True:
            msg = prompt(f"{nickname}: ")
            mensagem = f"{nickname}: {msg}"
            topico = "Chat_Texto"
            pub_socket.send_multipart([topico.encode(), mensagem.encode()])
            time.sleep(0.5)
