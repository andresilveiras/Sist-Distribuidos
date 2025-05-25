# Videoconferência com canais de vídeo, áudio e texto com ZeroMQ

Este projeto implementa um sistema de comunicação ponto-a-ponto com suporte a troca de **mensagens de texto, vídeo e áudio em tempo real** por um modelo **Publish-Subscribe** (sem o uso de broker) na linguagem **Python** com a biblioteca **ZeroMQ**.

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
├── video.py         # Módulo com funções de envio/recepção de vídeo
├── utils.py         # Módulo para tratar argumentos da linha de comando
└── README.md        # Este arquivo
```

---

## ⚙️ Requisitos

Instale as dependências com:

```bash
pip install pyzmq numpy prompt_toolkit sounddevice opencv-python
```

> Obs: o `sounddevice` pode exigir bibliotecas de sistema no Linux (ex: `portaudio`).

---

## ▶️ Como Executar

```bash
python3 main.py <Nickname> <PortaLocal> <Peer1[:Porta1]> [Peer2[:Porta2]] [--audio] [--video]
```

### Argumentos obrigatórios:
- `<Nickname>`: Nome de exibição do usuário no chat. Ex: `Alice`
- `<PortaLocal>`: Porta local usada para escutar mensagens de texto. Ex: `6000`
- `<Peer[:Porta]>`: IP e porta de outro participante. Se a porta não for especificada, usa `localhost`.

### Flags opcionais:
- `--audio`: Ativa o canal de áudio
- `--video`: Ativa o canal de vídeo

> O canal de texto é sempre ativado por padrão.

### Exemplo: Terminal 1 (Usuário A)

```bash
python3 main.py Alice 6000 192.168.0.11:6001 --audio --video
```

### Exemplo: Terminal 2 (Usuário B)

```bash
python3 main.py Bob 6001 192.168.0.10:6000 --audio --video
```
Onde: 
* `192.168.0.10:6000`  é o IP:Porta da máquina A
* `192.168.0.11:6001`  é o IP:Porta da máquina B

### Portas utilizadas automaticamente:
- **Texto**: Porta principal (ex: 6000)
- **Áudio**: `porta_texto + 1000` (ex: 6000 → 7000)
- **Vídeo**: `porta_texto + 2000` (ex: 6000 → 8000)

> É possível localizar os endereços de IP com o comando `hostname -I`.

---

## 🎧 Funcionalidades

- **Mensagens de Texto**: com interface fluida no terminal via `prompt_toolkit`
- **Transmissão de Áudio**: captura e reprodução em tempo real entre os peers
- **Transmissão de Vídeo**: via webcam com compressão JPEG
- **Tópicos nomeados**: `Chat_Texto`, `Chat_Audio`, `Chat_Video` para canais separados
- **Conexão via IP real**: funciona em redes locais sem precisar de broker central
- **Execução personalizável**: usuário escolhe quais canais quer ativar

---

## 🧪 Teste de IP na rede local

Para descobrir seu IP local:

```bash
hostname -I
```

Para verificar se a máquina B consegue se comunicar com a A:

```bash
ping 192.168.0.10
```

---

## 📝 TODO

- Interface gráfica (GUI)

---
