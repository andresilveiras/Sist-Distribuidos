
from multiprocessing import Process
import redis
import time
import uuid
import random
import os
import signal
import sys

r = redis.Redis(host='localhost', port=6379, db=0)
RESOURCE_KEY = "lock:recurso"
LOCK_TIMEOUT = 5

def acquire_lock(lock_id, timeout=LOCK_TIMEOUT):
    return r.set(RESOURCE_KEY, lock_id, nx=True, ex=timeout)

def release_lock(lock_id):
    if r.get(RESOURCE_KEY) == lock_id.encode():
        r.delete(RESOURCE_KEY)
        return True
    return False

def processo_simulado(nome):
    while True:
        time.sleep(random.uniform(1, 3))
        lock_id = str(uuid.uuid4())

        if acquire_lock(lock_id):
            print(f"[{nome}] ➡️ Entrou na região crítica")
            time.sleep(random.uniform(1, 2))
            print(f"[{nome}] ⬅️ Saiu da região crítica")
            release_lock(lock_id)
        else:
            print(f"[{nome}] ⏳ Esperando acesso...")

if __name__ == "__main__":
    nomes = ["P1", "P2", "P3"]
    processos = []

    for nome in nomes:
        p = Process(target=processo_simulado, args=(nome,))
        p.start()
        processos.append(p)

    try:
        for p in processos:
            p.join()
    except KeyboardInterrupt:
        print("\nEncerrando...")
        for p in processos:
            p.terminate()
        sys.exit(0)
