
# 🔒 Exclusão Mútua Distribuída com Redis

Este projeto demonstra como usar o **Redis como mecanismo de coordenação distribuída** para controlar o acesso a um **recurso compartilhado** entre múltiplos "processos" (simulados com threads).

Utilizamos um **lock distribuído simples** implementado com o comando `SET NX EX`, que garante exclusão mútua de forma segura e eficiente.

## 🧠 Conceito

O Redis é usado aqui para garantir que **somente um processo por vez** possa acessar a **região crítica**, usando:

- `SET key value NX EX timeout`: cria um lock apenas se não existir (`NX`) e com tempo de expiração (`EX`).
- `DEL key`: remove o lock ao sair da região crítica.

## 📄 Arquivo principal

- **`lock_redis.py`** – simula três processos tentando acessar um recurso protegido por um lock no Redis.

## 🚀 Como executar

### 1. Requisitos

- Python 3.7+
- Redis rodando localmente (padrão: `localhost:6379`)
- Biblioteca Python `redis`

### 2. Instalação

Instale o Redis com Docker (ou nativamente):

```bash
docker run -p 6379:6379 redis
```

Instale a biblioteca Python necessária:

```bash
pip install redis
```

### 3. Execução

Execute o script:

```bash
python lock_redis.py
```

Você verá no terminal os processos entrando e saindo da região crítica.

Para interromper, use `Ctrl + C`.

## 🔍 O que o programa faz?

- Três "processos" (`P1`, `P2`, `P3`) competem por um lock no Redis.
- Apenas um pode acessar a região crítica por vez.
- O lock expira automaticamente após 5 segundos, evitando deadlocks.
- Os processos continuam tentando acessar indefinidamente.

## 📚 Referências

- [Redis SET NX EX](https://redis.io/commands/set/)
- [Redis Distributed Lock](https://redis.io/docs/manual/patterns/distributed-locks/)
- [Redlock Algorithm (avançado)](https://redis.io/docs/reference/patterns/redlock/)

**Divirta-se explorando sistemas distribuídos com Redis!** 🚀🔁
