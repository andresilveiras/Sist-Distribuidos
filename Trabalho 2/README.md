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

Cada linha consome partes de forma aleatória conforme os produtos são fabricados ao longo do dia até o fechamento da ordem de produção (tamanha do lote). O estoque de partes deve apontar nível de estoque VERDE, AMARELO, VERMELHO (kanban) - quando o nível se aproxima do nível vermelho é necessário que o Almoxarifado dispare ordem de reabastecimento para fornecedores.

Usar: Docker containeres para cada entidade (Depósito de produtos acabados, Fabricas, linhas, almoxarifado, fornecedores) Criar Buffer estoque onde Consumo faz CheckOut (decrementa) e Abastecimento faz CheckIn (incrementa). Todo buffer de materiais e produtos deve ser mostrado em tela com seu valor atual e COR. Toda mensagem de pedidos de reabastecimento e ordem de produção deve usar MQTT entre entidades na 1ª versão do projeto – a versão final deve usar banco de dados em memória (ex. REDIS) ou RabbitMQ (justificar e explicar a escolha), compartilhado entre as entidades. 

## 🎯 Cenário Atual

Esta versão implementa uma versão completa do cenário proposto, combinando a **Fábrica 1 (Fabricação Empurrada)** com a simulação de demanda que irá "puxar" a produção da **Fábrica 2** por meio de uma **Central de Vendas**, que simula vendas de quantidades e tipos de produto aleatórios em um determinado período de tempo:

- **1 Fornecedor (`supplier`)**: Atende aos pedidos de reabastecimento do almoxarifado. Atualmente trabalha com 5 workers simultâneos em uma pool de threads.
- **1 Almoxarifado (`warehouse`)**: Gerencia o estoque de **100 tipos de peças** diferentes.
- **Fábrica 1 com 5 Linhas de Produção**: Cada linha é um contêiner (`factory1_line1` a `factory1_line5`) configurado para produzir um lote de 60 unidades de um produto específico (Pv1 a Pv5).
- **1 Centro de Vendas (`sales_center`)**: Simula a demanda diária de clientes, gerencia o estoque de produtos acabados e emite ordens de produção para a Fábrica 2.
- **Fábrica 2 com 5 Linhas de Produção**: Cada linha é um contêiner (`factory2_line1` a `factory2_line5`) configurado para produzir um lote de 25 unidades de um produto específico (Pv1 a Pv5) determinado pelo status AMARELO do estoque de produtos acabados gerenciados pelo Centro de Vendas.
- **1 Broker MQTT (`broker`)**: Centraliza toda a comunicação entre as entidades.
- **1 Dashboard de Monitoramento (`dashboard`)**: Uma interface web que exibe o status do sistema em tempo real, incluindo o estoque de peças, o progresso das linhas e o estoque de produtos acabados.

## 📁 Estrutura dos Arquivos

```plaintext
Trabalho 2/
├── broker/
│   ├── config/
│   │   └── mosquitto.conf  # Configurações do broker MQTT
│   └── Dockerfile
├── entities/
│   ├── dashboard/
│   │   ├── static/
│   │   │   └── style.css   # Estilo do dashboard em CSS   
│   │   ├── templates/
│   │   │   └── index.html  # Layout do dashboard em HTML
│   │   ├── Dockerfile
│   │   └── main.py         # Lógica (back-end) do dashboard em Python (Flask)
│   ├── factory1/line/
│   │   ├── Dockerfile
│   │   └── main.py         # Lógica da linha de produção da Fábrica 1
│   ├── factory2/line/
│   │   ├── Dockerfile
│   │   └── main.py         # Lógica da linha de produção da Fábrica 2
│   ├── sales_center/
│   │   ├── Dockerfile
│   │   └── main.py         # Lógica de simulação de vendas e demanda
│   ├── supplier/
│   │   ├── Dockerfile
│   │   └── main.py         # Lógica do fornecedor
│   └── warehouse/
│       ├── Dockerfile
│       └── main.py         # Lógica do almoxarifado
├── shared/
│   ├── buffer.py           # Classe do Buffer de estoque com lógica Kanban
│   ├── mqtt_client.py      # Helper para criar clientes MQTT
│   └── products.py         # Definição dos produtos e suas peças (BOM) 
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
3. Acesse o dashboard em seu navegador para monitorar a simulação: **http://localhost:5000**
4. Observe os logs no terminal. Para encerrar a simulação, pressione `Ctrl+C`.

## ⚙️ Funcionamento da Simulação

A simulação agora representa um ciclo de produção e consumo mais completo, com um "relógio" central ditando o ritmo:

1. **O "Dia" Começa**: O `sales_center` atua como o relógio do sistema. A cada "dia" (intervalo de tempo configurável), ele publica uma mensagem `simulation/new_day`. No momento o tempo está configurado para 10 minutos.
2. **Produção Empurrada (Fábrica 1)**: Ao receber o sinal de "novo dia", as 5 linhas da Fábrica 1 iniciam a produção de seus lotes fixos de 60 produtos. Para cada unidade, elas solicitam as peças necessárias ao `warehouse`.
3. **Demanda e Vendas**: Simultaneamente, o `sales_center` simula vendas de produtos, decrementando o estoque de produtos acabados.
4. **Reabastecimento do Estoque de Produtos**: Quando uma linha da Fábrica 1 conclui seu lote, ela notifica o `sales_center`, que adiciona os produtos recém-fabricados ao estoque central.
5. **Produção Puxada (Ordens para Fábrica 2)**: Após simular as vendas, o `sales_center` verifica o nível do estoque de produtos acabados. Se algum produto está abaixo da meta (nível Amarelo), ele emite uma ordem de produção no tópico `factory2/production_order`. Esta ordem é consumida pela Fábrica 2.
6. **Ciclo do Almoxarifado e Fornecedor**:
    - O `warehouse` atende aos pedidos de peças das linhas de produção.
    - Quando o estoque de uma peça fica baixo (nível AMARELO/VERMELHO), o `warehouse` emite uma ordem de reabastecimento para o `supplier`.
    - O `supplier` processa a ordem, simula um tempo de entrega e envia as peças para o `warehouse`, fechando o ciclo de suprimentos.
7. **Monitoramento Visual**: Todas as atualizações (estoque de peças, progresso das linhas, estoque de produtos acabados) são publicadas em tópicos `dashboard/*`. O serviço do `dashboard` captura essas mensagens e as exibe em tempo real na interface web.

## 🛠️ Tecnologias

- Python
- MQTT (Eclipse Mosquitto)
- Docker / Docker Compose
- Flask & Flask-SocketIO (para o Dashboard)

## 🐞 Problemas Conhecidos

- Linhas de produção travadas quando o estoque de peças no almoxarifado chega a 0, mesmo após a reposição;

## 🔮 Próximos Passos

- Implementar um relatório de vendas / produção por dia
- Implementar um sistema de logs mais eficiente
- Implementar persistência de dados, conforme proposto (escolher entre Redis ou RabbitMQ)