# Aluno: Andre Silveira Sousa RA: 628239

import time
import zmq

while True:

    print("Iniciando o publisher...")
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    print("Aguardando conexão de subscribers...")

    msg = "hello world"

    while True:
        topic = input("Digite o tópico: ")
        msg = input("Envie mensagem para o tópico informado: ")
        socket.send_string(f"{topic} {msg}")
