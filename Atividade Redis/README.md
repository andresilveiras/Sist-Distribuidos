
# 🔒 Exclusão Mútua Distribuída com Redis (com multiprocessing)

Este projeto demonstra como usar o **Redis como mecanismo de coordenação distribuída** para controlar o acesso a um **recurso compartilhado**, agora utilizando **processos reais** (`multiprocessing`) ao invés de threads.

## 🧠 Conceito

Cada processo tenta obter um **lock distribuído** no Redis usando:

- `SET key value NX EX timeout`: cria um lock apenas se não existir (`NX`) e com tempo de expiração (`EX`).
- `DEL key`: libera o lock ao sair da região crítica.

## 📄 Arquivo principal

- **`lock_redis.py`** – simula três processos distintos acessando um recurso compartilhado de forma coordenada via Redis.

## 🚀 Como executar

### 1. Requisitos

- Python 3.7+
- Redis rodando localmente (padrão: `localhost:6379`)
- Biblioteca Python `redis`

### 2. Instalação

Inicie o Redis com Docker:

```bash
docker run -p 6379:6379 redis
```

Instale o cliente Redis para Python:

```bash
pip install redis
```

### 3. Execução

```bash
python lock_redis.py
```

Para parar a execução, pressione `Ctrl + C`. Os processos serão finalizados corretamente.

## 🔍 O que o programa faz?

- Três processos (`P1`, `P2`, `P3`) competem por um lock no Redis.
- Apenas um entra na região crítica por vez.
- O lock expira automaticamente após 5 segundos.
- Simula concorrência real com `multiprocessing`.

## 📚 Referências

- [Redis SET NX EX](https://redis.io/commands/set/)
- [Redis Distributed Lock](https://redis.io/docs/manual/patterns/distributed-locks/)

**Explore sistemas distribuídos com segurança e controle! 🚀**
