# Distributed Manufacturing - Sistema Distribuído de Produção

Este projeto simula uma planta de manufatura com múltiplas linhas de produção, controle de estoque de partes e produtos acabados, e comunicação entre entidades via MQTT.

## 🧱 Estrutura Inicial
- **Fornecedor**
- **Almoxarifado**
- **Fábrica 1 (Linha 1)**
- **Broker MQTT (Mosquitto)**

## 🚀 Como Executar
1. Instale o Docker e Docker Compose
2. Clone este repositório
3. Execute:
   ```bash
   docker-compose up --build
   ```

## 📡 Comunicação
As entidades trocam mensagens via tópicos MQTT. Ex:
- `estoque/check_out`
- `estoque/check_in`
- `ordem/producao`

## 📦 Estoque
Cada parte tem um buffer com limite verde/amarelo/vermelho (Kanban).

## 🛠️ Tecnologias
- Python
- MQTT (Eclipse Mosquitto)
- Docker / Docker Compose

