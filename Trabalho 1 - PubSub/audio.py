"""
audio_sync.py  ·  Áudio em tempo real com sincronização A/V
-----------------------------------------------------------
* Captura microfone (20 ms) => Opus 32 kb/s
* Envia via ZeroMQ PUB com fila máx. = 1
* Recebe, espera AUDIO_DELAY (25 ms) e toca

┌───────────────┬──────────────────────┐
│ double little │  payload             │
│ endian (8 B)  │                      │
│ timestamp ts  │  • Áudio: quadro Opus│
│               │    (≈ 70-120 B)      │
│               │  • Vídeo: JPEG Q60   │
│               │    480×270 (≈ 15 KB) │
└───────────────┴──────────────────────┘

"""

import time, struct, zmq, opuslib, sounddevice as sd, numpy as np

SAMPLE_RATE    = 48_000
CHANNELS       = 1
FRAME_DURATION = 0.02                 # 20 ms
FRAME_SIZE     = int(SAMPLE_RATE * FRAME_DURATION)   # 960
BITRATE        = 32_000               # bps
AUDIO_DELAY    = 0.025                # 25 ms  (== VIDEO_DELAY)

def send_audio(context, peer_audio_endpoints, stop_event):
    pub = context.socket(zmq.PUB)

    pub.setsockopt(zmq.SNDHWM,   1)  # fila de saída = 1 pacote
    pub.setsockopt(zmq.CONFLATE, 1)  # sobrescreve pacote antigo
    pub.setsockopt(zmq.IMMEDIATE, 1) # descarta caso SUB não esteja pronto
    pub.setsockopt(zmq.LINGER,    0) # fecha imediatamente

    for ep in peer_audio_endpoints:
        pub.connect(f"tcp://{ep}")
    time.sleep(1)  # tempo p/ SUB se inscrever

    enc = opuslib.Encoder(SAMPLE_RATE, CHANNELS, opuslib.APPLICATION_AUDIO)
    enc.bitrate = BITRATE

    def callback(indata, frames, time_info, status):
        if stop_event.is_set():
            raise sd.CallbackStop()
        packet = enc.encode(indata.tobytes(), FRAME_SIZE)
        payload = struct.pack("<d", time.time()) + packet
        try:
            pub.send(payload, flags=zmq.NOBLOCK | zmq.DONTWAIT, copy=False)
        except zmq.Again:
            pass  # descarta para manter latência

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype='int16', blocksize=FRAME_SIZE,
                        latency='low', callback=callback):
        while not stop_event.is_set():
            time.sleep(0.1)

    pub.close()

def receive_audio(context, listen_audio_port, stop_event):
    sub = context.socket(zmq.SUB)

    sub.setsockopt(zmq.RCVHWM,   10)   # até 10 pacotes pendentes
    sub.setsockopt(zmq.CONFLATE, 1)    # sempre o mais recente

    sub.setsockopt(zmq.SUBSCRIBE, b"")
    sub.bind(f"tcp://0.0.0.0:{listen_audio_port}")

    dec = opuslib.Decoder(SAMPLE_RATE, CHANNELS)
    out = sd.OutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                          dtype='int16', blocksize=FRAME_SIZE, latency='low')
    out.start()

    poller = zmq.Poller(); poller.register(sub, zmq.POLLIN)
    last_print, latest_mv = time.time(), None

    try:
        while not stop_event.is_set():
            if sub in dict(poller.poll(20)):   # verifica se o socket possui dados pendentes
                try:
                    while True:                # drena todas as mensagens e guarda apenas a ultima
                        latest_mv = memoryview(sub.recv(flags=zmq.NOBLOCK, copy=False))
                except zmq.Again:
                    pass

            if latest_mv is None:
                continue

            ts = struct.unpack_from("<d", latest_mv, 0)[0]
            opus_bytes = bytes(latest_mv[8:])
            wait = (ts + AUDIO_DELAY) - time.time()
            if wait > 0:
                time.sleep(wait)

            pcm = dec.decode(opus_bytes, FRAME_SIZE, decode_fec=False)
            out.write(np.frombuffer(pcm, np.int16).reshape(-1, 1))

            #now = time.time()
            #if now - last_print > 2:
                #print(f"[AUDIO] latência ≈ {(now - ts)*1000:.0f} ms")
                #last_print = now
            latest_mv = None
    finally:
        out.stop(); out.close(); sub.close()

