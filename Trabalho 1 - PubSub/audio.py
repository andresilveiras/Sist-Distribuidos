import zmq
import time
import sounddevice as sd
import numpy as np

'''
Função send_audio
Envia áudio para o tópico "Chat_Audio".
'''

def send_audio(context, peer_audio_endpoints):
    pub_socket = context.socket(zmq.PUB)
    pub_topic = "Chat_Audio"

    for endpoint in peer_audio_endpoints:
        pub_socket.connect(f"tcp://{endpoint}")
    time.sleep(1)

    def callback(indata, frames, time_info, status):
        if status:
            print("Erro de entrada de áudio:", status)
        pub_socket.send_multipart([pub_topic.encode(), indata.tobytes()])

    with sd.InputStream(samplerate=44100, channels=1, callback=callback, dtype='int16'):
        while True:
            time.sleep(0.1)

'''
Função receive_audio
Recebe áudio do tópico "Chat_Audio" e o reproduz.
'''

def receive_audio(context, listen_audio_port):
    sub_topic = "Chat_Audio"
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://0.0.0.0:{listen_audio_port}")
    sub_socket.setsockopt(zmq.SUBSCRIBE, sub_topic.encode())

    while True:
        topic, data_bytes = sub_socket.recv_multipart()
        if topic == sub_topic.encode():
            audio_data = np.frombuffer(data_bytes, dtype='int16')
            sd.play(audio_data, samplerate=44100)
