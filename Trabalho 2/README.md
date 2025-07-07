# Trabalho 2 - Sistema Distribuído de Produção

Este projeto simula uma planta de manufatura com múltiplas linhas de produção, controle de estoque de partes e produtos acabados, e comunicação entre entidades via MQTT.

O projeto foi desenvolvido para o segundo trabalho da disciplina Sistemas Distribuídos da Universidade Federal de São Carlos, no primeiro semestre de 2025.

Alunos:

- André Silveira Sousa
- Josué Martins da Conceição
- Lucas Arruk Mendes

Professor: Dr. Fredy João Valente

## Descrição do Trabalho

Objetivo: Garantir que não ocorra ruptura na fabricação por falta de partes.

Cenário: Uma empresa possuí 2 unidades fabris: fábrica 1 com 5 linhas de produção e fábrica 2 com 8 linhas de produção. A empresa fabrica 1 produto em 5 versões diferentes (Pv1, Pv2, Pv3, Pv4, Pv5).

Cada produto possuí uma configuração composta por uma somatória de partes: kit base composto por 43 partes e kit variação composto por uma somatória de partes que variam de 20 a 33 partes dependendo da versão. O total de partes diferentes usadas na fabricação = 100.

Projeto: Desenvolver solução de monitoramento de nível de estoque de partes em cada linha de produção. A fabrica 1 produz os 5 produtos todos os dias com ordens de produção com tamanho de lote de 60 produtos por linha (Fabricação Empurrada). A fabrica 2 fabrica os 5 produtos, porém o tamanho do lote e o produto fabricado variam dia a dia dependendo dos pedidos do mercado (Fabricação Puxada).

A solução deve simular pedidos de produtos dia a dia (aleatório) e calcular quantos produtos devem ser fabricados em função do estoque de cada produto acabado. Deve portanto monitorar nível de estoque de produtos (1 a 5), consumos (via pedido), lote de fabricação para o dia (lista de partes enviado para almoxarifado), abastecimento de partes nas linhas e monitoramento de estoques de partes em cada linha para cada parte. 

Cada linha consome parte de forma aleatória conforme os produtos são fabricados ao longo do dia até o fechamento da ordem de produção (tamanha do lote). O estoque de partes deve apontar nível de estoque VERDE, AMARELO, VERMELHO (kanban) - quando o nível se aproxima do nível vermelho é necessário disparar ordem de reabastecimento para o Almoxarifado.

monitorar nível de estoque de partes no almoxarifado usando mesma estratégia de Kanban - quando nível se aproximar do vermelho, deve-se emitir ordem de comprar para fornecedores.

Usar: Docker containeres para cada entidade (Depósito de produtos acabados, Fabricas, linhas, almoxarifado, fornecedores) Criar Buffer estoque onde Consumo faz CheckOut (decrementa) e Abastecimento faz CheckIn (incrementa). Todo buffer de materiais e produtos deve ser mostrado em tela com seu valor atual e COR. Toda mensagem de pedidos de reabastecimento e ordem de produção deve usar MQTT entre entidades na 1ª versão do projeto – a versão final deve usar banco de dados em memória (ex. REDIS) ou RabbitMQ (justificar e explicar a escolha), compartilhado entre as entidades. 

Sugestão: desenhar solução para 1 fornecedor, 1 almoxarifado, 1 fábrica com1 linha e 1 produto com 53 partes e depois escalar para cenário do projeto

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

