# Aluno: Andre Silveira Sousa RA: 628239

import zmq


print("Iniciando subscriber…")
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5555")

print("Conexao ativa.")

topic = input("Digite o tópico de interesse: ")
socket.setsockopt_string(zmq.SUBSCRIBE, topic)

while True:
    message = socket.recv_string()
    print("Recebido:", message)


print("Conexao fechada.")

'''
import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5555")  # Conecta ao publisher

topic_filter = "chat"
socket.setsockopt_string(zmq.SUBSCRIBE, topic_filter)

print("Esperando mensagens...")

while True:
    message = socket.recv_string()
    print("Recebido:", message)

'''