# Aluno: Andre Silveira Sousa RA: 628239

import socket

HOST = '127.0.1.1'              # Endereco IP do Servidor
PORT = 9999                     # Porta que o Servidor esta

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #cria um socket p/ internet via TCP
endereco = (HOST, PORT)

tcp.connect(endereco)

print("Conexao ativa.")
print("00 encerra o chat.")

msg = input("Digite seu apelido: ")

while msg != '00':
    tcp.send(msg.encode())     
    msg = input("Mensagem: ")

tcp.close()

print("Conexao fechada.")