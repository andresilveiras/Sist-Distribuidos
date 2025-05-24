import time
from prompt_toolkit import prompt
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import print_formatted_text
import zmq

'''
Função send_messages
Envia mensagens de texto para o tópico "Chat_Texto".
'''

def send_messages(context, nickname, peer_endpoints, stop_event):
    pub_socket = context.socket(zmq.PUB)
    pub_topic = "Chat_Texto"
    for endpoint in peer_endpoints:
        pub_socket.connect(f"tcp://{endpoint}")
    time.sleep(1)
    print(f"Olá {nickname}!\nDigite uma mensagem para conversar!\nPara sair, pressione Ctrl+C.")

    with patch_stdout():
        while not stop_event.is_set():
            mensagem = prompt(f"{nickname}: ")
            pub_socket.send_multipart([pub_topic.encode(), nickname.encode(), mensagem.encode()])
            time.sleep(0.5)
        pub_socket.close()

'''
Função receive_messages
Recebe mensagens de texto do tópico "Chat_Texto" e as imprime na tela.
'''

def receive_messages(context, listen_port, stop_event):
    sub_topic = "Chat_Texto"
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://0.0.0.0:{listen_port}")
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, sub_topic)

    while not stop_event.is_set():
        topico, nickname, mensagem = sub_socket.recv_multipart()
        if topico.decode() == sub_topic:
            print_formatted_text(nickname.decode() + ": " + mensagem.decode())
    sub_socket.close()
