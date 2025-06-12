import redis
import time
import uuid
import random

# Conexão com o Redis
r = redis.Redis(host='localhost', port=6379, db=0)

RESOURCE_KEY = "lock:recurso"
LOCK_TIMEOUT = 5  # segundos

def acquire_lock(lock_id, timeout=LOCK_TIMEOUT):
    # Tenta adquirir lock com uma chave única
    return r.set(RESOURCE_KEY, lock_id, nx=True, ex=timeout)

def release_lock(lock_id):
    # Verifica se ainda é o dono do lock antes de liberar
    if r.get(RESOURCE_KEY) == lock_id.encode():
        r.delete(RESOURCE_KEY)
        return True
    return False

def processo_simulado(nome):
    while True:
        time.sleep(random.uniform(1, 3))  # Espera aleatória antes de tentar
        lock_id = str(uuid.uuid4())  # ID único do lock

        if acquire_lock(lock_id):
            print(f"[{nome}] ➡️ Entrou na região crítica")
            time.sleep(random.uniform(1, 2))  # Região crítica
            print(f"[{nome}] ⬅️ Saindo da região crítica")
            release_lock(lock_id)
        else:
            print(f"[{nome}] ⏳ Esperando acesso...")

if __name__ == "__main__":
    import threading

    nomes = ["P1", "P2", "P3"]
    threads = []

    for nome in nomes:
        t = threading.Thread(target=processo_simulado, args=(nome,))
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nEncerrando...")
