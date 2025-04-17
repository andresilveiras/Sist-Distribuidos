import socket

hostname = socket.gethostname()
iplocal = socket.gethostbyname(hostname)
print(iplocal)

HOST = iplocal              # Endereco IP do Servidor
PORT = 9999                 # Porta que o Servidor esta

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #cria um socket p/ internet via TCP
endereco = (HOST, PORT)

tcp.bind(endereco)          
tcp.listen()  

while True:
    conexao, cliente = tcp.accept()
    nick = conexao.recv(1024)
    print(cliente , "conectou-se como ", nick.decode())
    while True:
        msg = conexao.recv(1024)
        if not msg: break
        print(nick.decode(), " enviou a mensagem: ", msg.decode())
    print("Finalizando conexao do cliente " , cliente)
    conexao.close()