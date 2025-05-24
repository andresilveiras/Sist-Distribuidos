import zmq
import time
import sounddevice as sd
import numpy as np

'''
Função send_audio
Envia áudio para o tópico "Chat_Audio".
'''

def send_audio(context, audio_peer_endpoints, stop_event):
    pub_socket = context.socket(zmq.PUB)
    pub_topic = "Chat_Audio"

    for endpoint in audio_peer_endpoints:
        pub_socket.connect(f"tcp://{endpoint}")
    time.sleep(1)

    duration = 0.2  # 200 ms de áudio por pacote (~8820 samples com 44100 Hz)

    try:
        #print("Iniciando captura de áudio...")
        while not stop_event.is_set():
            audio = sd.rec(int(duration * 44100), samplerate=44100, channels=1, dtype='int16')
            sd.wait()  # Espera o término da gravação
            pub_socket.send_multipart([pub_topic.encode(), audio.tobytes()])
            #print(f"Enviado pacote de {len(audio)} samples")
    except Exception as e:
        print("Erro no envio de áudio:", e)
    finally:
        pub_socket.close()

'''
Função receive_audio
Recebe áudio do tópico "Chat_Audio" e o reproduz.
'''

def receive_audio(context, listen_audio_port, stop_event):
    sub_topic = "Chat_Audio"
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://0.0.0.0:{listen_audio_port}")
    sub_socket.setsockopt(zmq.SUBSCRIBE, sub_topic.encode())

    poller = zmq.Poller()
    poller.register(sub_socket, zmq.POLLIN)

    try:
        #print("Esperando áudio...")
        while not stop_event.is_set():
            events = dict(poller.poll(timeout=100))
            if sub_socket in events:
                topic, data_bytes = sub_socket.recv_multipart()
                if topic.decode() == sub_topic:
                    audio_data = np.frombuffer(data_bytes, dtype='int16')
                    audio_data = audio_data.reshape(-1, 1)  # Garante shape (n, 1) para mono
                    sd.play(audio_data, samplerate=44100)
                    sd.wait()  # evita erro de finalização
    except Exception as e:
        print("Erro no recebimento de áudio:", e)
    finally:
        sub_socket.close()
