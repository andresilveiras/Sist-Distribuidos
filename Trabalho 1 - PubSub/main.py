import zmq
import threading
from texto import send_messages, receive_messages
from audio import send_audio, receive_audio
from video import send_video, receive_video
from utils import parse_args

nickname, listen_port, peer_endpoints, audio_peer_endpoints, video_peer_endpoints = parse_args()
context = zmq.Context()

# Recepção
threading.Thread(target=receive_messages, args=(context, listen_port), daemon=True).start()
threading.Thread(target=receive_audio, args=(context, listen_port + 1000), daemon=True).start()
threading.Thread(target=receive_video, args=(context, listen_port + 2000), daemon=True).start()

# Envio
threading.Thread(target=send_audio, args=(context, audio_peer_endpoints), daemon=True).start()
threading.Thread(target=send_video, args=(context, video_peer_endpoints), daemon=True).start()
send_messages(context, nickname, peer_endpoints)
