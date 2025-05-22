import zmq, threading, time, sys

PEER_ID, PORT = sys.argv[1], int(sys.argv[2])
ALL_PEERS = {
    "peer1": ("127.0.0.1", 5551),
    "peer2": ("127.0.0.1", 5552),
    "peer3": ("127.0.0.1", 5553),
    "peer4": ("127.0.0.1", 5554),
}

def router_loop(ctx):
    router = ctx.socket(zmq.ROUTER)
    router.bind(f"tcp://*:{PORT}")
    print(f"[{PEER_ID}] ROUTER listening on {PORT}")

    while True:
        sender, msg = router.recv_multipart()        # exactly 2 parts
        print(f"[{sender.decode()}] {msg.decode()}")

def dealer_loop(ctx):
    # one DEALER per remote peer → true broadcast
    dealers = {}
    for pid, (ip, port) in ALL_PEERS.items():
        if pid == PEER_ID:
            continue
        d = ctx.socket(zmq.DEALER)
        d.setsockopt_string(zmq.IDENTITY, PEER_ID)
        d.connect(f"tcp://{ip}:{port}")
        dealers[pid] = d
        print(f"[{PEER_ID}] connected to {pid} at {ip}:{port}")

    time.sleep(1)                                   # let sockets settle
    while True:
        text = input()
        if not text:
            continue
        for d in dealers.values():                  # broadcast
            d.send_string(text)                     # ONE frame only

def main():
    ctx = zmq.Context.instance()
    threading.Thread(target=router_loop, args=(ctx,), daemon=True).start()
    threading.Thread(target=dealer_loop,  args=(ctx,), daemon=True).start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()

