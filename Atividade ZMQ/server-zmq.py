# Aluno: Andre Silveira Sousa RA: 628239

import time
import zmq

while True:

    print("Iniciando o servidor...")
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    print("Aguardando conexão do cliente...")

    nick = socket.recv()
    print(nick.decode(), "conectou-se")
    msg = "OK"
    while msg != "00":
        socket.send(msg.encode())
        msg = socket.recv().decode()
        if not msg:break
        print(nick.decode(), "enviou a mensagem: ", msg)
    print (nick.decode(), "desconectou-se.")
    print("A conexão do cliente foi encerrada")
    socket.close()

