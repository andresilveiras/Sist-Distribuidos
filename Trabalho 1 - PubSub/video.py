"""
video_sync.py · Vídeo JPEG 480×270 @ 15 fps sincronizado ao áudio
-----------------------------------------------------------------
* Captura câmera => JPEG Q60
* Envia via ZeroMQ PUB (fila = 1)
* Recebe, drena backlog, espera VIDEO_DELAY e exibe

┌───────────────┬──────────────────────┐
│ double little │  payload             │
│ endian (8 B)  │                      │
│ timestamp ts  │  • Áudio: quadro Opus│
│               │    (≈ 70-120 B)      │
│               │  • Vídeo: JPEG Q60   │
│               │    480×270 (≈ 15 KB) │
└───────────────┴──────────────────────┘

"""

import os, time, struct, cv2, zmq, numpy as np

# Para evitar erro do plugin Qt no venv
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", "/usr/lib64/qt5/plugins")

WIDTH, HEIGHT  = 480, 270
JPEG_QUALITY   = 60
TARGET_FPS     = 15
VIDEO_DELAY    = 0.025          # 25 ms  (== AUDIO_DELAY)

def send_video(context, peer_video_endpoints, stop_event):
    pub = context.socket(zmq.PUB)

    pub.setsockopt(zmq.SNDHWM, 1)    # máx. 1 pacote pendente
    pub.setsockopt(zmq.CONFLATE, 1)  # substitui pacote anterior
    pub.setsockopt(zmq.IMMEDIATE, 1) # descarta se SUB não pronto
    pub.setsockopt(zmq.LINGER, 0)    # fecha rápido

    for ep in peer_video_endpoints:
        pub.connect(f"tcp://{ep}")
    time.sleep(1)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)      # evita fila interna da webcam

    enc_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    frame_int = 1 / TARGET_FPS
    next_t = time.time()

    while not stop_event.is_set():
        ret, frame = cap.read()  # le o frame
        if not ret:
            continue
        ok, jpg = cv2.imencode('.jpg', frame, enc_param) # codifica em JPEG
        if not ok:
            continue

        payload = struct.pack("<d", time.time()) + jpg.tobytes() # cria o payload
        try:
            pub.send(payload, flags=zmq.NOBLOCK | zmq.DONTWAIT, copy=False)
        except zmq.Again:
            pass  # descarta quadro atrasado

        # correcao para o fps
        next_t += frame_int
        sleep = next_t - time.time()
        if sleep > 0:
            time.sleep(sleep)
        else:
            next_t = time.time()

    cap.release(); pub.close()

def receive_video(context, listen_video_port, stop_event):
    sub = context.socket(zmq.SUB)

    sub.setsockopt(zmq.RCVHWM, 1)
    sub.setsockopt(zmq.CONFLATE, 1)
    
    sub.setsockopt(zmq.SUBSCRIBE, b"")
    sub.bind(f"tcp://0.0.0.0:{listen_video_port}")

    cv2.namedWindow("Vídeo", cv2.WINDOW_NORMAL)
    last_print, latest_mv = time.time(), None

    while not stop_event.is_set():
        try:
            while True:
                latest_mv = memoryview(sub.recv(flags=zmq.NOBLOCK, copy=False)) # so mantem o quadro mais recente
        except zmq.Again:
            pass

        if latest_mv is None:
            time.sleep(0.005); continue

        # sincronizacao com o audio
        ts = struct.unpack_from("<d", latest_mv, 0)[0]
        wait = (ts + VIDEO_DELAY) - time.time()
        if wait > 0:
            time.sleep(wait)

        # constroi e exibe os frames
        npimg = np.frombuffer(latest_mv[8:], np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        if frame is not None:
            cv2.imshow("Vídeo", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        #now = time.time()
        #if now - last_print > 2:
            #print(f"[VIDEO] latência ≈ {(now - ts)*1000:.0f} ms")
            #last_print = now
        latest_mv = None

    cv2.destroyAllWindows(); sub.close()

