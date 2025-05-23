import time
from prompt_toolkit import prompt
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import print_formatted_text
import zmq

'''
Função receive_messages
Recebe mensagens de texto do tópico "Chat_Texto" e as imprime na tela.
'''

def receive_messages(context, listen_port):
    sub_topic = "Chat_Texto"
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://0.0.0.0:{listen_port}")
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, sub_topic)

    while True:
        topico, mensagem = sub_socket.recv_multipart()
        if topico == sub_topic.encode():
            print_formatted_text(mensagem.decode())

'''
Função send_messages
Envia mensagens de texto para o tópico "Chat_Texto".
'''

def send_messages(context, nickname, peer_endpoints):
    pub_socket = context.socket(zmq.PUB)
    pub_topic = "Chat_Texto"
    for endpoint in peer_endpoints:
        pub_socket.connect(f"tcp://{endpoint}")
    time.sleep(1)
    print(f"Olá {nickname}!\nDigite uma mensagem para conversar!")

    with patch_stdout():
        while True:
            msg = prompt(f"{nickname}: ")
            mensagem = f"{nickname}: {msg}"
            pub_socket.send_multipart([pub_topic.encode(), mensagem.encode()])
            time.sleep(0.5)
