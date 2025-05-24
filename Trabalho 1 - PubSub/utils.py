import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Sistema de videoconferência com texto, áudio e vídeo no modelo Pub/Sub com conexão direta entre peers.")
    parser.add_argument("nickname", help="Identificador do usuário (nome ou apelido)")
    parser.add_argument("listen_port", type=int, help="Porta local para escutar mensagens de texto")
    parser.add_argument("peers", nargs="*", help="Lista de peers no formato IP:PORTA ou apenas PORTA para localhost")
    parser.add_argument("--audio", action="store_true", help="Ativa o canal de áudio")
    parser.add_argument("--video", action="store_true", help="Ativa o canal de vídeo")
    args = parser.parse_args()

    peer_endpoints = []
    audio_peer_endpoints = []
    video_peer_endpoints = []

    for arg in args.peers:
        if ':' in arg:
            ip, port = arg.split(':')
        else:
            ip, port = '127.0.0.1', arg

        peer_endpoints.append(f"{ip}:{port}")
        audio_peer_endpoints.append(f"{ip}:{int(port) + 1000}")
        video_peer_endpoints.append(f"{ip}:{int(port) + 2000}")

    return (
        args.nickname,
        args.listen_port,
        peer_endpoints,
        audio_peer_endpoints,
        video_peer_endpoints,
        args.audio,
        args.video
    )
