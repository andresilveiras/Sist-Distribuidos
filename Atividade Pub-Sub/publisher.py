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

    while msg != "00":
        topic = input("Digite o tópico: ")
        msg = input("Envie mensagem para o tópico ", topic, ":")
        socket.send_string(f"{topic} {msg}")
    socket.close()

'''
import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")  # Porta 5555 para enviar mensagens

# Espera para garantir que os subscribers se conectem
time.sleep(1)

while True:
    topic = "chat"
    message = input("Mensagem para enviar: ")
    socket.send_string(f"{topic} {message}")

'''