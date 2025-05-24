import sys

def parse_args():
    if len(sys.argv) < 3:
        print("Uso: python3 main.py <Nome> <PortaLocal> <Peer1[:Porta]> [Peer2[:Porta]] ...")
        sys.exit(1)

    nickname = sys.argv[1]
    listen_port = int(sys.argv[2])
    peer_args = sys.argv[3:]

    peer_endpoints = []
    audio_peer_endpoints = []
    video_peer_endpoints = []

    for arg in peer_args:
        if ':' in arg:
            ip, port = arg.split(':')
        else:
            ip, port = '127.0.0.1', arg

        peer_endpoints.append(f"{ip}:{port}")
        audio_peer_endpoints.append(f"{ip}:{int(port) + 1000}")
        video_peer_endpoints.append(f"{ip}:{int(port) + 2000}")

    return nickname, listen_port, peer_endpoints, audio_peer_endpoints, video_peer_endpoints
