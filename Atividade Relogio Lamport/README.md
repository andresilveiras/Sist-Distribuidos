
# Exclusão Mútua Distribuída com Relógio Lógico (Lamport)

Este projeto demonstra um exemplo de coordenação entre **processos distribuídos** para acessar uma **região crítica** usando um algoritmo de **exclusão mútua distribuída** com **relógio lógico de Lamport**.

## 📚 O que este programa faz?

- Simula três processos (`P1`, `P2` e `P3`) que competem pelo acesso a um recurso compartilhado.
- Cada processo:
  - Envia pedidos de acesso aos outros processos.
  - Espera pela permissão de todos antes de entrar na região crítica.
  - Executa a região crítica (simulada com um tempo de espera aleatório).
  - Libera o recurso para que outros possam entrar.
- O relógio lógico de Lamport é usado para ordenar os eventos em um ambiente distribuído, sem um relógio físico centralizado.

## 🏗️ Estrutura

- **`main.py`**: Código principal que executa a simulação.

## 🚀 Como executar

1. Clone este repositório (ou copie o arquivo `main.py`).
2. Execute no terminal:
   ```bash
   python main.py
   ```
3. Observe as mensagens no terminal mostrando o funcionamento passo a passo.
4. Para parar a simulação, pressione `Ctrl + C`.

## ⚙️ Requisitos

- Python 3 (testado com Python 3.8+).
- Nenhuma biblioteca externa é necessária — apenas a biblioteca padrão do Python.

## 💡 Conceitos principais

- **Exclusão mútua distribuída**: Garante que apenas um processo por vez acesse a região crítica.
- **Relógio lógico de Lamport**: Usado para ordenar eventos e resolver conflitos de pedidos de entrada.

## 🧩 Possíveis melhorias

- Adicionar logs em arquivo.
- Aumentar o número de processos ou alterar os tempos de espera para estudar o comportamento.
- Implementar detecção de falhas.

---

**Divirta-se estudando e simulando sistemas distribuídos! 🚀**
