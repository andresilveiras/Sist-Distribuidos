# Aluno: Andre Silveira Sousa RA: 628239

import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")


while True:
    nick = socket.recv()
    print(nick.decode(), "conectou-se")
    resp = "OK"
    while True:
        socket.send(resp.encode())
        msg = socket.recv()
        if not msg:break
        print(nick.decode(), "enviou a mensagem: ", msg.decode())
    print (nick.decode(), "desconectou-se.")
    print("A conexão do cliente foi encerrada")
    socket.close()
