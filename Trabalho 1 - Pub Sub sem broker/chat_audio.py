import zmq
import threading
import time
import sys
import sounddevice as sd
import numpy as np

'''
Função: receive_messages
Recebe as mensagens de texto do tópico "Chat_Texto"
'''

def receive_messages(context, listen_port):
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://0.0.0.0:{listen_port}")
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "Chat_Texto")

    while True:
        msg = sub_socket.recv_string()
        print(msg)

'''
Função: send_messages
Envia as mensagens de texto para todos os peers inscritos no tópico "Chat_Texto"
'''

def send_messages(context, identity, peer_endpoints):
    pub_socket = context.socket(zmq.PUB)

    for endpoint in peer_endpoints:
        pub_socket.connect(f"tcp://{endpoint}")

    time.sleep(1)
    print(f"Olá {identity}!\nDigite uma mensagem para conversar!")

    while True:
        print("Sua mensagem: ")
        msg = input()
        topic = "Chat_Texto"
        mensagem = f"{topic} {identity}: {msg}"
        pub_socket.send_string(mensagem)
        time.sleep(0.5)

'''
Função: receive_audio
Recebe os áudios enviados no tópico "Chat_Audio"
'''

def receive_audio(context, listen_audio_port):
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://0.0.0.0:{listen_audio_port}")    
    sub_socket.setsockopt(zmq.SUBSCRIBE, b"Chat_Audio")

    while True:
        topic, data_bytes = sub_socket.recv_multipart()
        if topic == b"Chat_Audio":
            audio_data = np.frombuffer(data_bytes, dtype='int16')
            sd.play(audio_data, samplerate=44100)


'''
Função: send_audio
Envia os áudios para os incritos no tópico "Chat_Audio"
'''        

def send_audio(context, peer_audio_endpoints):
    pub_socket = context.socket(zmq.PUB)
    

    for endpoint in peer_audio_endpoints:
        pub_socket.connect(f"tcp://{endpoint}")
    time.sleep(1)

    def callback(indata, frames, time_info, status):
        if status:
            print("Audio Input Error:", status)
        data_bytes = indata.tobytes()
        topic = b"Chat_Audio"
        pub_socket.send_multipart([topic, data_bytes])
        #pub_socket.send(data_bytes)

    with sd.InputStream(samplerate=44100, channels=1, callback=callback, dtype='int16'):
        while True:
            time.sleep(0.1)


# ========== PARÂMETROS ==========

# Execução esperada:
# python3 chat_audio.py <Nome> <PortaLocal> <Peer1[:Porta]> [Peer2[:Porta]] ...


if len(sys.argv) < 3:
    print("Uso: python3 chat_audio.py <Nome> <PortaLocal> <Peer1[:Porta]> [Peer2[:Porta]] ...")
    sys.exit(1)

identity = sys.argv[1]
listen_port = int(sys.argv[2])
peer_args = sys.argv[3:]

peer_endpoints = []
audio_peer_endpoints = []

for arg in peer_args:
    if ':' in arg:
        ip, port = arg.split(':')
    else:
        ip, port = '127.0.0.1', arg
    peer_endpoints.append(f"{ip}:{port}")
    audio_peer_endpoints.append(f"{ip}:{int(port) + 1000}")

context = zmq.Context()

# Iniciar threads para recepção de mensagens e áudio
threading.Thread(target=receive_messages, args=(context, listen_port), daemon=True).start()
threading.Thread(target=receive_audio, args=(context, listen_port + 1000), daemon=True).start()

# Iniciar threads de envio de mensagens e áudio
threading.Thread(target=send_audio, args=(context, audio_peer_endpoints), daemon=True).start()
send_messages(context, identity, peer_endpoints)
