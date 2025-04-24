# Aluno: Andre Silveira Sousa RA: 628239

import zmq

context = zmq.Context()

#  Socket to talk to server
print("Connecting to server…")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

print("Conexao ativa.")
print("00 encerra o chat.")

msg = input("Digite seu apelido: ")

while msg != "00":
    socket.send(msg.encode())  
    resp = socket.recv()
    msg = input("Mensagem: ")
socket.send(msg.encode())
socket.close()

print("Conexao fechada.")
