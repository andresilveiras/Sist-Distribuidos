import zmq
import time
import threading
from texto import send_messages, receive_messages
from audio import send_audio, receive_audio
from video import send_video, receive_video
from utils import parse_args

(
    nickname,
    listen_port,
    peer_endpoints,
    audio_peer_endpoints,
    video_peer_endpoints,
    use_audio,
    use_video
) = parse_args()

context = zmq.Context()
stop_event = threading.Event()

# Sempre ativa o canal de texto
threading.Thread(target=receive_messages, args=(context, listen_port, stop_event), daemon=True).start()

# Ativa canais de áudio e vídeo somente se solicitados
if use_audio:
    threading.Thread(target=receive_audio, args=(context, listen_port + 1000, stop_event), daemon=True).start()
    threading.Thread(target=send_audio, args=(context, audio_peer_endpoints, stop_event), daemon=True).start()

if use_video:
    threading.Thread(target=receive_video, args=(context, listen_port + 2000, stop_event), daemon=True).start()
    threading.Thread(target=send_video, args=(context, video_peer_endpoints, stop_event), daemon=True).start()

# Captura a saída limpa
try:
    send_messages(context, nickname, peer_endpoints, stop_event)
except KeyboardInterrupt:
    print("\nEncerrando...")
    stop_event.set()
    time.sleep(1)