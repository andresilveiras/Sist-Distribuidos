# Chat de Texto e Áudio com ZeroMQ

Este projeto implementa um sistema de comunicação ponto-a-ponto com suporte a troca de **mensagens de texto** e **áudio em tempo real** por um modelo **Publish-Subscribe** (sem o uso de broker) na linguagem **Python** com a biblioteca **ZeroMQ**

O projeto foi desenvolvido para o primeiro trabalho da disciplina Sistemas Distribuídos da Universidade Federal de São Carlos, no primeiro semestre de 2025.

Alunos:

- André Silveira Sousa 
- Josué Martins da Conceição
- Lucas Arruk Mendes

Professor: Dr. Fredy João Valente

---

## 📁 Estrutura dos Arquivos

```
Trabalho 1 - PubSub/
├── main.py          # Script principal que executa o chat completo
├── texto.py         # Módulo com funções de envio/recepção de texto
├── audio.py         # Módulo com funções de envio/recepção de áudio
├── utils.py         # Módulo para tratar argumentos da linha de comando
└── README.md        # Este arquivo
```

---

## ⚙️ Requisitos

Instale as dependências com:

```bash
pip install pyzmq sounddevice numpy prompt_toolkit
```

> Obs: o `sounddevice` pode exigir bibliotecas de sistema no Linux (ex: `portaudio`).

---

## ▶️ Como Executar

### Execução padrão:

```bash
python3 main.py <Nickname> <PortaLocal> <Peer1[:Porta1]> [Peer2[:Porta2]] ...
```

Onde:

- **Nickname**: É o nome de exibição do usuário host no chat. Ex: `Alice`
- **PortaLocal**: É a porta que será utilizada no host local para a comunicação. Ex: `6000`
- **Peer1**: Endereço de IP na rede local do usuário 1 (o outro usuário ao qual o host irá se comunicar). Ex: `192.168.0.10`
- **Porta1**: Porta de comunicação TCP para o IP atribuído. Ex: `6001`

O áudio será transmitido automaticamente por uma porta paralela `porta_texto + 1000`. Ex: 6000 → 7000.

### Exemplo: Terminal 1 (Usuário A)

```bash
python3 main.py Alice 6000 192.168.0.11:6001
```

### Exemplo: Terminal 2 (Usuário B)

```bash
python3 main.py Bob 6001 192.168.0.10:6000
```

> Neste exemplo, `192.168.0.10` é o endereço de IP na rede local da máquina do usuário A, e `192.168.0.11` é o endereço de IP na rede local da máquina do usuário B. 

É possível localizar os endereços de IP com o comando `hostname -I`. 

---

## 🎧 Funcionalidades

* **Mensagens de Texto**: com interface fluida no terminal via `prompt_toolkit`.
* **Transmissão de Áudio**: captura e reprodução em tempo real entre os peers.
* **Tópicos nomeados**: `Chat_Texto` e `Chat_Audio` para separar os canais.
* **Conexão via IP real**: funciona em redes locais sem precisar de broker central.

---

## 🧪 Teste de IP na rede local

Para descobrir seu IP local:

```bash
hostname -I
```

Para testar se a máquina B enxerga a A:

```bash
ping 192.168.0.10
```

---

## 📝 TODO

- Adicionar canal de vídeo
- Manejo das threads quando um canal/usuário cai

---

