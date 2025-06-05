# main.py

import time
import random
import threading

# Constantes de mensagem
ENTER = "ENTER"
ALLOW = "ALLOW"
RELEASE = "RELEASE"

# Canal de comunicação simples
class Channel:
    def __init__(self):
        self.processes = {}

    def register(self, process_id, process):
        self.processes[process_id] = process

    def sendTo(self, recipients, message):
        for r in recipients:
            self.processes[r].receive(message)

# Classe de processo
class Process(threading.Thread):
    def __init__(self, process_id, otherProcess, channel):
        super().__init__()
        self.process_id = process_id
        self.otherProcess = otherProcess
        self.channel = channel
        self.queue = []
        self.clock = 0

    def requestToEnter(self):
        self.clock += 1
        self.queue.append((self.clock, self.process_id, ENTER))
        print(f"[Processo {self.process_id}] Quer entrar (clock={self.clock})")
        self.channel.sendTo(self.otherProcess, (self.clock, self.process_id, ENTER))

    def allowToEnter(self, requester):
        self.clock += 1
        print(f"[Processo {self.process_id}] Permite {requester} (clock={self.clock})")
        self.channel.sendTo([requester], (self.clock, self.process_id, ALLOW))

    def release(self):
        self.queue = [r for r in self.queue if not (r[1] == self.process_id and r[2] == ENTER)]
        self.clock += 1
        print(f"[Processo {self.process_id}] Libera recurso (clock={self.clock})")
        self.channel.sendTo(self.otherProcess, (self.clock, self.process_id, RELEASE))

    def allowedToEnter(self):
        commProcess = set(r[1] for r in self.queue if r[2] == ALLOW)
        return self.queue and self.queue[0][1] == self.process_id and len(self.otherProcess) == len(commProcess)

    def receive(self, message):
        clock, sender_id, action = message
        self.clock = max(self.clock, clock) + 1
        if action == ENTER:
            self.queue.append((clock, sender_id, ENTER))
            self.allowToEnter(sender_id)
        elif action == ALLOW:
            self.queue.append((clock, sender_id, ALLOW))
        elif action == RELEASE:
            self.queue = [r for r in self.queue if not (r[1] == sender_id and r[2] == ENTER)]
            print(f"[Processo {self.process_id}] Remove pedido de {sender_id} após RELEASE (clock={self.clock})")

        print(f"[Processo {self.process_id}] Recebeu {action} de {sender_id} (clock={self.clock})")

    def run(self):
        while True:
            # Espera aleatória antes de tentar entrar
            time.sleep(random.uniform(1, 3))

            self.requestToEnter()

            # Aguarda permissão de todos
            while not self.allowedToEnter():
                time.sleep(0.1)

            # Região crítica simulada
            print(f"[Processo {self.process_id}] *** Entrou na região crítica ***")
            time.sleep(random.uniform(1, 2))
            print(f"[Processo {self.process_id}] *** Saiu da região crítica ***")

            self.release()

# Simulação principal
if __name__ == "__main__":
    # Cria canal
    channel = Channel()

    # Cria processos
    p1 = Process(1, [2, 3], channel)
    p2 = Process(2, [1, 3], channel)
    p3 = Process(3, [1, 2], channel)

    # Registra processos no canal
    channel.register(1, p1)
    channel.register(2, p2)
    channel.register(3, p3)

    # Inicia threads dos processos
    print("\n--- Início da Simulação ---\n--- Pressione Ctrl+C para encerrar ---\n")
    time.sleep(1)  # Pequena pausa para garantir que tudo esteja pronto
    p1.start()
    p2.start()
    p3.start()

    # Aguarda manualmente (Ctrl+C para encerrar)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n--- Fim da Simulação ---\n")
