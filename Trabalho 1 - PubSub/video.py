import cv2
import zmq
import base64
import numpy as np
import time

'''
Função send_video
Envia vídeo para o tópico "Chat_Video".
'''

def send_video(context, peer_video_endpoints, stop_event):
    pub_socket = context.socket(zmq.PUB)
    pub_topic = "Chat_Video"

    for endpoint in peer_video_endpoints:
        pub_socket.connect(f"tcp://{endpoint}")
    time.sleep(1)

    cap = cv2.VideoCapture(0)
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        pub_socket.send_multipart([pub_topic.encode(), buffer.tobytes()])
        time.sleep(0.03)  # Envio em ~30 FPS
     # Libera os recursos no acionamento de stop_event
    cap.release()
    pub_socket.close()

''' 
Função receive_video
Recebe vídeo do tópico "Chat_Video" e o exibe.
'''

def receive_video(context, listen_video_port, stop_event):
    sub_topic = "Chat_Video"
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(f"tcp://0.0.0.0:{listen_video_port}")
    sub_socket.setsockopt(zmq.SUBSCRIBE, sub_topic.encode())

    while not stop_event.is_set():
        topic, frame_bytes = sub_socket.recv_multipart()
        if topic.decode() == sub_topic:
            npimg = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
            cv2.imshow("Video recebido", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    # Libera os recursos no acionamento de stop_event
    cv2.destroyAllWindows()
    sub_socket.close()
