#!/usr/bin/env python3
"""
peer_video.py – text chat + voice + webcam video over a ZeroMQ P2P mesh
========================================================================
*Three* identical peers connect in a full‑mesh ROUTER/DEALER topology, the
same architecture you used for `peer_voice.py`.  Each process:

  •  Captures microphone audio (16‑kHz mono PCM, 20‑ms frames)
  •  Captures webcam frames (default cam, 320×240 @10 fps)
  •  Sends both streams plus typed text to every remote peer
  •  Plays audio with a small jitter buffer (<=60 ms)
  •  Displays the latest video frame from every peer in its own OpenCV
     window ("peerX")

Dependencies
------------
    pip install pyzmq sounddevice opencv-python

No codec libraries are required – audio is raw PCM; video frames are JPEG‑
compressed with OpenCV (quality=65 → ~15–30 kB per frame).

Usage (three terminals)
----------------------
    python peer_video.py peer1 5551
    python peer_video.py peer2 5552
    python peer_video.py peer3 5553

Press <Enter> to send chat text.  Ctrl‑C to quit.
"""
from __future__ import annotations

import cv2
import numpy as np
import sounddevice as sd
import zmq, threading, queue, time, sys, signal

# ----------------------------------------------------------------------------
# Peer configuration ---------------------------------------------------------
# ----------------------------------------------------------------------------
PEER_ID, PORT = sys.argv[1], int(sys.argv[2])
ALL_PEERS = {
    "peer1": ("127.0.0.1", 5551),
    "peer2": ("127.0.0.1", 5552),
    "peer3": ("127.0.0.1", 5553),
}
assert PEER_ID in ALL_PEERS, f"Unknown peer: {PEER_ID}"

# Audio constants
SAMPLE_RATE   = 16_000
FRAME_MS      = 20
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000
FRAME_BYTES   = FRAME_SAMPLES * 2  # int16 mono

# Video constants
WIDTH, HEIGHT = 320, 240
FPS            = 10
JPEG_QUALITY   = 65  # 0‑100
VIDEO_PERIOD   = 1.0 / FPS

# Queues
send_pcm_q   : queue.Queue[bytes] = queue.Queue(maxsize=200)
play_pcm_q   : queue.Queue[bytes] = queue.Queue(maxsize=200)
send_img_q   : queue.Queue[bytes] = queue.Queue(maxsize=100)

# Stop flag
stop_event = threading.Event()

ctx = zmq.Context.instance()

# ----------------------------------------------------------------------------
# ROUTER – receive from others ------------------------------------------------
# ----------------------------------------------------------------------------
print(f"[{PEER_ID}] running on port {PORT} – chat+audio+video")

def router_loop():
    router = ctx.socket(zmq.ROUTER)
    router.bind(f"tcp://*:{PORT}")
    poller = zmq.Poller()
    poller.register(router, zmq.POLLIN)

    # For video display we keep last frame per peer
    last_frame: dict[str, np.ndarray] = {}

    while not stop_event.is_set():
        events = dict(poller.poll(10))  # 10‑ms tick
        if router in events and events[router] & zmq.POLLIN:
            try:
                sender, tag, payload = router.recv_multipart(zmq.NOBLOCK)
            except zmq.Again:
                continue

            tag = tag.decode()
            if tag == 'T':  # text
                print(f"[{sender.decode()}] {payload.decode()}")
            elif tag == 'A':  # audio PCM
                if play_pcm_q.full():
                    play_pcm_q.get_nowait()
                play_pcm_q.put_nowait(payload)
            elif tag == 'V':  # JPEG video frame
                np_arr = np.frombuffer(payload, dtype=np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if frame is not None:
                    last_frame[sender.decode()] = frame
            else:
                print(f"[warn] unknown tag {tag}")

        # --- refresh OpenCV windows (non‑blocking) ---
        for pid, frame in last_frame.items():
            cv2.imshow(pid, frame)
        if cv2.waitKey(1) & 0xFF == 27:  # Esc key closes video windows
            stop_event.set()
            break

    router.close(0)

# ----------------------------------------------------------------------------
# DEALERs – one per remote peer (broadcast) ----------------------------------
# ----------------------------------------------------------------------------

def dealer_loop():
    dealers: dict[str, zmq.Socket] = {}
    for pid, (ip, port) in ALL_PEERS.items():
        if pid == PEER_ID:
            continue
        d = ctx.socket(zmq.DEALER)
        d.setsockopt_string(zmq.IDENTITY, PEER_ID)
        d.setsockopt(zmq.SNDHWM, 256)
        d.connect(f"tcp://{ip}:{port}")
        dealers[pid] = d
        print(f"[{PEER_ID}] connected to {pid} at {ip}:{port}")

    poller = zmq.Poller()
    for d in dealers.values():
        poller.register(d, zmq.POLLOUT)

    last_video_ts = 0.0
    cap = cv2.VideoCapture(0, cv2.CAP_ANY)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    while not stop_event.is_set():
        # ------------------------------------------------------------------
        # 1. Send any queued audio frames (non‑blocking)
        # ------------------------------------------------------------------
        try:
            pcm = send_pcm_q.get_nowait()
            frame = [b'A', pcm]        # tag A = audio
            for d in dealers.values():
                try:
                    d.send_multipart(frame, flags=zmq.DONTWAIT, copy=False)
                except zmq.Again:
                    pass  # drop if pipe full
        except queue.Empty:
            pass

        # ------------------------------------------------------------------
        # 2. Capture + send video at ~FPS
        # ------------------------------------------------------------------
        now = time.time()
        if now - last_video_ts >= VIDEO_PERIOD:
            ok, frame = cap.read()
            if ok:
                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                enc_ok, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                if enc_ok:
                    jpg_bytes = buf.tobytes()
                    for d in dealers.values():
                        try:
                            d.send_multipart([b'V', jpg_bytes], flags=zmq.DONTWAIT, copy=False)
                        except zmq.Again:
                            pass
                last_video_ts = now

        # ------------------------------------------------------------------
        # 3. Poll stdin for text (non‑blocking)
        # ------------------------------------------------------------------
        if sys.stdin in select_select([sys.stdin], [], [], 0)[0]:
            text = sys.stdin.readline().strip()
            if text:
                for d in dealers.values():
                    d.send_multipart([b'T', text.encode()], flags=zmq.DONTWAIT)

        time.sleep(0.001)  # tiny sleep to yield CPU

    cap.release()
    for d in dealers.values():
        d.close(0)

# ----------------------------------------------------------------------------
# Audio capture & playback ---------------------------------------------------
# ----------------------------------------------------------------------------

def record_audio():
    def cb(indata, frames, time_info, status):
        if stop_event.is_set():
            raise sd.CallbackStop()
        if not send_pcm_q.full():
            send_pcm_q.put_nowait(bytes(indata))
    sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16',
        blocksize=FRAME_SAMPLES,
        callback=cb,
    ).start()


def play_audio():
    """Play PCM from queue; keep ≤3 frames for low latency."""
    def cb(outdata, frames, time_info, status):
        # Drop excess frames (keep latest ≤3)
        while play_pcm_q.qsize() > 3:
            play_pcm_q.get_nowait()
        try:
            pcm = play_pcm_q.get_nowait()
        except queue.Empty:
            pcm = b'\x00' * FRAME_BYTES
        outdata[:] = pcm
        if stop_event.is_set():
            raise sd.CallbackStop()
    sd.RawOutputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16',
        blocksize=FRAME_SAMPLES,
        callback=cb,
    ).start()

# ----------------------------------------------------------------------------
# Helper: non‑blocking stdin select (cross‑platform) -------------------------
# ----------------------------------------------------------------------------
import os
import selectors
sel = selectors.DefaultSelector()
sel.register(sys.stdin, selectors.EVENT_READ)

def select_select(r, w, x, timeout):
    events = sel.select(timeout)
    if events:
        return ([sys.stdin], [], [])
    return ([], [], [])

# ----------------------------------------------------------------------------
# Main -----------------------------------------------------------------------
# ----------------------------------------------------------------------------

def main():
    # Handle Ctrl‑C cleanly
    def sigint_handler(sig, frame):
        stop_event.set()
    signal.signal(signal.SIGINT, sigint_handler)

    # Launch threads
    threading.Thread(target=router_loop, daemon=True).start()
    threading.Thread(target=dealer_loop, daemon=True).start()
    threading.Thread(target=record_audio, daemon=True).start()
    threading.Thread(target=play_audio, daemon=True).start()

    # Keep main thread alive until stop_event is set
    while not stop_event.is_set():
        time.sleep(0.2)

    ctx.term()
    cv2.destroyAllWindows()
    print("[info] shut down cleanly")


if __name__ == "__main__":
    main()

