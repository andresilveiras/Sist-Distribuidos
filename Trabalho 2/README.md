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

## 🎯 Cenário Atual (Simplificado)

Esta versão implementa o cenário da **Fábrica 1 (Fabricação Empurrada)**:

- **1 Fornecedor (`supplier`)**: Atende aos pedidos de reabastecimento do almoxarifado.
- **1 Almoxarifado (`warehouse`)**: Gerencia o estoque de **100 tipos de peças** diferentes.
- **Fábrica 1 com 5 Linhas de Produção**: Cada linha é um contêiner (`factory1_line1` a `factory1_line5`) configurado para produzir um lote de 60 unidades de um produto específico (Pv1 a Pv5).
- **1 Broker MQTT (`broker`)**: Centraliza toda a comunicação entre as entidades.
- **1 Dashboard de Monitoramento (`dashboard`)**: Uma interface web que exibe o status do sistema em tempo real.

## 📁 Estrutura dos Arquivos

```plaintext
Trabalho 2/
├── broker/
│   ├── config/
│   │   └── mosquitto.conf  # Configurações do broker (logs, etc.)
│   └── Dockerfile
├── entities/
│   ├── dashboard/
│   │   ├── templates/
│   │   │   └── index.html
│   │   ├── Dockerfile
│   │   └── main.py         
│   ├── factory1/line/
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

A simulação agora representa um sistema de produção completo, com monitoramento visual:

1. **Produção**: Cada uma das 5 linhas de produção começa a trabalhar em seu lote de 60 produtos. Para montar uma unidade, a linha solicita ao almoxarifado, uma por uma, todas as peças definidas na sua "Lista de Materiais" (BOM).
2. **Consumo de Estoque**: O almoxarifado recebe os pedidos de peças via tópico `estoque/check_out`. Se a peça está disponível, ele a envia e notifica a linha via `estoque/status`. Se não há estoque, ele notifica a falta, e a linha de produção para.
3. **Feedback e Controle**: A linha de produção só continua a montagem ao receber a confirmação de que a peça foi enviada. Se a produção é parada por falta de uma peça, ela só é retomada quando o almoxarifado avisa que o estoque foi normalizado.
4. **Kanban e Reabastecimento**: Quando o estoque de qualquer uma das 100 peças no almoxarifado atinge o nível **VERMELHO**, ele dispara uma ordem de compra no tópico `estoque/reabastecer`.
5. **Atuação do Fornecedor**: O fornecedor recebe a ordem, simula um tempo de entrega e envia as peças para o almoxarifado via tópico `estoque/check_in`, completando o ciclo.
6. **Monitoramento Visual**: Todas as atualizações de estoque e progresso das linhas são publicadas em tópicos `dashboard/*`. O serviço do dashboard captura essas mensagens e as exibe em tempo real na interface web.

## 🛠️ Tecnologias

- Python
- MQTT (Eclipse Mosquitto)
- Docker / Docker Compose
- Flask & Flask-SocketIO (para o Dashboard)

## 🔮 Próximos Passos

- Implementar a Fábrica 2 (Fabricação Puxada).