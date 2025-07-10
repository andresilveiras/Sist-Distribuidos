# Trabalho 2 - Sistema Distribuído de Produção

Este projeto simula uma planta de manufatura com múltiplas linhas de produção, controle de estoque de partes e produtos acabados, e comunicação entre entidades via MQTT.

O projeto foi desenvolvido para o segundo trabalho da disciplina Sistemas Distribuídos da Universidade Federal de São Carlos, no primeiro semestre de 2025.

Alunos:

- André Silveira Sousa
- Josué Martins da Conceição
- Lucas Arruk Mendes

Professor: Dr. Fredy João Valente

## Descrição do Trabalho

**Objetivo Final:** Garantir que não ocorra ruptura na fabricação por falta de partes em um cenário complexo com múltiplas fábricas, linhas e produtos.

Cenário: Uma empresa possuí 2 unidades fabris: fábrica 1 com 5 linhas de produção e fábrica 2 com 8 linhas de produção. A empresa fabrica 1 produto em 5 versões diferentes (Pv1, Pv2, Pv3, Pv4, Pv5).

Cada produto possuí uma configuração composta por uma somatória de partes: kit base composto por 43 partes e kit variação composto por uma somatória de partes que variam de 20 a 33 partes dependendo da versão. O total de partes diferentes usadas na fabricação = 100.

Projeto: Desenvolver solução de monitoramento de nível de estoque de partes em cada linha de produção. A fabrica 1 produz os 5 produtos todos os dias com ordens de produção com tamanho de lote de 60 produtos por linha (Fabricação Empurrada). A fabrica 2 fabrica os 5 produtos, porém o tamanho do lote e o produto fabricado variam dia a dia dependendo dos pedidos do mercado (Fabricação Puxada).

A solução deve simular pedidos de produtos dia a dia (aleatório) e calcular quantos produtos devem ser fabricados em função do estoque de cada produto acabado. Deve portanto monitorar nível de estoque de produtos (1 a 5), consumos (via pedido), lote de fabricação para o dia (lista de partes enviado para almoxarifado), abastecimento de partes nas linhas e monitoramento de estoques de partes em cada linha para cada parte. 

Cada linha consome parte de forma aleatória conforme os produtos são fabricados ao longo do dia até o fechamento da ordem de produção (tamanha do lote). O estoque de partes deve apontar nível de estoque VERDE, AMARELO, VERMELHO (kanban) - quando o nível se aproxima do nível vermelho é necessário disparar ordem de reabastecimento para o Almoxarifado.

monitorar nível de estoque de partes no almoxarifado usando mesma estratégia de Kanban - quando nível se aproximar do vermelho, deve-se emitir ordem de comprar para fornecedores.

Usar: Docker containeres para cada entidade (Depósito de produtos acabados, Fabricas, linhas, almoxarifado, fornecedores) Criar Buffer estoque onde Consumo faz CheckOut (decrementa) e Abastecimento faz CheckIn (incrementa). Todo buffer de materiais e produtos deve ser mostrado em tela com seu valor atual e COR. Toda mensagem de pedidos de reabastecimento e ordem de produção deve usar MQTT entre entidades na 1ª versão do projeto – a versão final deve usar banco de dados em memória (ex. REDIS) ou RabbitMQ (justificar e explicar a escolha), compartilhado entre as entidades. 

## 🎯 Cenário Atual (Simplificado)

Seguindo a sugestão do escopo, a versão atual implementa um ciclo de produção e reabastecimento completo para validar a arquitetura base:

- **1 Fornecedor (`supplier`)**: Por enquanto, apenas simula sua existência, sem reabastecer o estoque.
- **1 Almoxarifado (`warehouse`)**: Gerencia o estoque de um único item (`Parte A`).
- **1 Fábrica com 1 Linha de Produção (`factory1_line1`)**: Consome `Parte A` do almoxarifado em intervalos regulares.
- **1 Broker MQTT (`broker`)**: Centraliza toda a comunicação entre as entidades.

## 📁 Estrutura dos Arquivos

```
Trabalho 2/
├── broker/
│   ├── config/
│   │   └── mosquitto.conf  # Configurações do broker (logs, etc.)
│   └── Dockerfile
├── entities/
│   ├── factory1/line1/
│   │   ├── Dockerfile
│   │   └── main.py         # Lógica da linha de produção
│   ├── supplier/
│   │   ├── Dockerfile
│   │   └── main.py         # Lógica do fornecedor
│   └── warehouse/
│       ├── Dockerfile
│       └── main.py         # Lógica do almoxarifado
├── shared/
│   ├── buffer.py           # Classe do Buffer de estoque com lógica Kanban
│   └── mqtt_client.py      # Helper para criar clientes MQTT
├── docker-compose.yml      # Orquestra todos os contêineres
└── README.md               # Este arquivo
```

## ▶️ Como Executar

Certifique-se de que o **Docker** e o **Docker Compose** estão instalados em sua máquina.

1.  Clone este repositório.
2.  No terminal, navegue até a raiz do projeto e execute:
   ```bash
   docker-compose up --build
   ```
3.  Observe os logs no terminal. Para encerrar a simulação, pressione `Ctrl+C`.

## ⚙️ Funcionamento da Simulação

A simulação agora opera em um ciclo fechado de consumo e reabastecimento:

1.  **Consumo**: A **Linha de Produção** (`factory1_line1`) solicita 5 unidades da `Parte A` a cada 5 segundos, publicando um pedido no tópico `estoque/check_out`.
2.  **Processamento**: O **Almoxarifado** (`warehouse`) recebe o pedido, valida se há estoque e realiza o `check_out`. O novo status do estoque é exibido no console com um sistema de cores (Kanban): **<span style="color:green">VERDE</span>**, **<span style="color:yellow">AMARELO</span>** ou **<span style="color:red">VERMELHO</span>**.
3.  **Alerta de Nível Baixo**: Se o `check_out` faz o nível do estoque atingir o status **VERMELHO**, o almoxarifado publica uma ordem de compra no tópico `estoque/reabastecer`.
4.  **Atuação do Fornecedor**: O **Fornecedor** (`supplier`), que está inscrito neste tópico, recebe a ordem. Ele simula um tempo de entrega e, ao final, envia as peças publicando no tópico `estoque/check_in`.
5.  **Reabastecimento**: O **Almoxarifado** recebe as novas peças, realiza o `check_in` em seu buffer e normaliza o nível de estoque, completando o ciclo.

## 🛠️ Tecnologias
- Python
- MQTT (Eclipse Mosquitto)
- Docker / Docker Compose

## 🔮 Próximos Passos

- Implementar um mecanismo de feedback para que a linha de produção pare de solicitar peças quando o estoque estiver zerado.
- Adaptar o almoxarifado para gerenciar múltiplos tipos de peças simultaneamente.
- Escalar a solução para múltiplas linhas, produtos e peças, conforme o escopo completo do trabalho.
