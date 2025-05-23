#!/usr/bin/env python3
"""
peer_voice.py  –  text + raw‑PCM voice chat over ZeroMQ (stable edition)
======================================================================
This revision addresses the two remaining problems you saw:

  •  **Silent lock‑up** after ~10 s  → caused by the audio‑TX thread
     blocking when the network queue filled.  We now use a *poll + try‑send*
     loop and we *drop* audio if any pipe is congested.

  •  **Crash on Ctrl‑C** (threads raised ContextTerminated)  → we add a
     global `stop_evt`; all worker loops exit cleanly *before* the ØMQ
     context is terminated.

No changes to the user interface: run three terminals like

    python peer_voice.py peer1 5551
    python peer_voice.py peer2 5552
    python peer_voice.py peer3 5553

Dependencies (same):
    pip install pyzmq sounddevice   # plus PortAudio runtime libs
"""
from __future__ import annotations

import sys, time, threading, queue, zmq, argparse, signal

# ------------------------------------------------------------------
# CLI / PEER LIST ---------------------------------------------------
# ------------------------------------------------------------------
parser = argparse.ArgumentParser(description="P2P text + voice chat")
parser.add_argument("peer_id")
parser.add_argument("port", type=int)
parser.add_argument("--mute", action="store_true",
                    help="run without microphone / speaker (text‑only)")
args = parser.parse_args()

PEER_ID, PORT = args.peer_id, args.port
ALL_PEERS = {
    "peer1": ("127.0.0.1", 5551),
    "peer2": ("127.0.0.1", 5552),
    "peer3": ("127.0.0.1", 5553),
}

# ------------------------------------------------------------------
# OPTIONAL AUDIO ----------------------------------------------------
# ------------------------------------------------------------------
VOICE = False
try:
    if not args.mute:
        import sounddevice as sd  # noqa: F401 – grabs PortAudio.
        VOICE = True
except Exception as e:  # any import / runtime error → text‑only
    print(f"[audio] disabled: {e}", file=sys.stderr)

SAMPLE_RATE   = 16_000            # Hz, mono
FRAME_MS      = 20                # ms per packet
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000
FRAME_BYTES   = FRAME_SAMPLES * 2  # int16 little‑endian

# ------------------------------------------------------------------
# THREAD COMMUNICATION ---------------------------------------------
# ------------------------------------------------------------------
send_pcm_q: queue.Queue[bytes] = queue.Queue(maxsize=400)   # 8 s
play_pcm_q: queue.Queue[bytes] = queue.Queue(maxsize=400)
stop_evt    = threading.Event()  # global shutdown flag

# ------------------------------------------------------------------
# ØMQ SET‑UP --------------------------------------------------------
# ------------------------------------------------------------------
ctx      = zmq.Context.instance()
router   = ctx.socket(zmq.ROUTER)
router.setsockopt(zmq.RCVHWM, 4000)
router.bind(f"tcp://*:{PORT}")

# one DEALER per remote peer for real broadcast
DEALER_HWM = 4000

dealers: dict[str, zmq.Socket] = {}
for pid, (ip, prt) in ALL_PEERS.items():
    if pid == PEER_ID:
        continue
    d = ctx.socket(zmq.DEALER)
    d.setsockopt_string(zmq.IDENTITY, PEER_ID)
    d.setsockopt(zmq.SNDHWM, DEALER_HWM)
    d.connect(f"tcp://{ip}:{prt}")
    dealers[pid] = d

# ------------------------------------------------------------------
# AUDIO HELPERS -----------------------------------------------------
# ------------------------------------------------------------------
if VOICE:

    def record_audio() -> None:
        """Capture mic PCM and enqueue; drops frames if queue full."""
        def cb(indata, frames, time_, status):
            try:
                send_pcm_q.put_nowait(bytes(indata))
            except queue.Full:
                pass  # drop
        sd.RawInputStream(channels=1, samplerate=SAMPLE_RATE,
                          blocksize=FRAME_SAMPLES, dtype="int16",
                          callback=cb).start()

    def play_audio():
        """Plays PCM frames pulled from play_pcm_q (max 3 buffered)."""
        def cb(outdata, frames, time_info, status):
            # Keep at most 3 frames (≈ 60 ms); discard older ones
            while play_pcm_q.qsize() > 3:
                play_pcm_q.get_nowait()           # drop the oldest frame

            try:
                pcm = play_pcm_q.get_nowait()      # freshest frame
            except queue.Empty:
                pcm = b'\x00' * (frames * 2)       # silence

            outdata[:] = pcm                       # copy to soundcard buffer

        sd.RawOutputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='int16',
            blocksize=FRAME_SAMPLES,
            callback=cb
        ).start()
# ------------------------------------------------------------------
# NETWORK THREADS ---------------------------------------------------
# ------------------------------------------------------------------

TEXT_TAG  = b'T'
VOICE_TAG = b'P'  # P = PCM


def router_loop() -> None:
    poller = zmq.Poller()
    poller.register(router, zmq.POLLIN)
    while not stop_evt.is_set():
        socks = dict(poller.poll(100))   # 100 ms tick
        if router not in socks:
            continue
        try:
            frames = router.recv_multipart(flags=zmq.NOBLOCK)
        except zmq.Again:
            continue
        if len(frames) < 3:
            continue
        sender, tag, payload = frames[:3]
        if tag == TEXT_TAG:
            print(f"[{sender.decode()}] {payload.decode()}")
        elif tag == VOICE_TAG and VOICE:
            try:
                play_pcm_q.put_nowait(payload)
            except queue.Full:
                pass


def audio_tx_loop() -> None:
    """Ship PCM frames to every peer; drop if any pipe congested."""
    while not stop_evt.is_set() and VOICE:
        try:
            pcm = send_pcm_q.get(timeout=0.1)
        except queue.Empty:
            continue
        frame = [VOICE_TAG, pcm]
        for sock in dealers.values():
            try:
                sock.send_multipart(frame, flags=zmq.DONTWAIT, copy=False)
            except zmq.Again:
                pass  # congested – drop for that peer


def stdin_loop() -> None:
    """Block on stdin; broadcast each non‑empty line."""
    for line in iter(sys.stdin.readline, ''):
        if stop_evt.is_set():
            break
        text = line.rstrip('\n')
        if not text:
            continue
        frame = [TEXT_TAG, text.encode()]
        for sock in dealers.values():
            sock.send_multipart(frame)
    stop_evt.set()  # EOF (e.g. Ctrl‑D)

# ------------------------------------------------------------------
# THREAD LAUNCH -----------------------------------------------------
# ------------------------------------------------------------------
threads: list[threading.Thread] = [
    threading.Thread(target=router_loop, daemon=True),
    threading.Thread(target=stdin_loop,  daemon=True),
]
if VOICE:
    threads += [
        threading.Thread(target=record_audio, daemon=True),
        threading.Thread(target=play_audio,   daemon=True),
        threading.Thread(target=audio_tx_loop, daemon=True),
    ]

for t in threads:
    t.start()

print(f"[{PEER_ID}] online  – voice {'ON' if VOICE else 'OFF'}  – Ctrl+C to quit")

# ------------------------------------------------------------------
# SHUTDOWN HANDLING -------------------------------------------------
# ------------------------------------------------------------------
try:
    while any(t.is_alive() for t in threads):
        time.sleep(0.2)
except KeyboardInterrupt:
    pass
finally:
    stop_evt.set()             # signal threads to exit
    for t in threads:
        t.join(timeout=1)
    ctx.term()                 # safe because all loops now stopped
    print("\nBye!")

