import random

# Define a lista de todas as 100 peças únicas disponíveis.
ALL_PARTS = [f"Part-{i:03d}" for i in range(1, 101)]

# Define o Kit Base com as primeiras 43 peças.
BASE_KIT = ALL_PARTS[0:43]

# Define os Kits de Variação para cada produto, usando as peças restantes.
# A soma das partes de variação deve ser 100 - 43 = 57.
# Distribuímos essas 57 peças entre os 5 produtos.
VARIATION_KITS = {
    "Pv1": ALL_PARTS[43:53],  # 10 peças
    "Pv2": ALL_PARTS[53:64],  # 11 peças
    "Pv3": ALL_PARTS[64:76],  # 12 peças
    "Pv4": ALL_PARTS[76:88],  # 12 peças
    "Pv5": ALL_PARTS[88:100], # 12 peças
}

# Cria a "Lista de Materiais" (Bill of Materials - BOM) para cada produto.
# Cada produto é composto pelo Kit Base mais seu Kit de Variação específico.
BOM = {
    product: BASE_KIT + variation_parts
    for product, variation_parts in VARIATION_KITS.items()
}

# Define o tamanho do lote de reabastecimento para cada peça.
# Cada peça terá um lote com uma quantidade aleatória entre 10 e 99.
PART_BATCH_SIZES = {
    part: random.randint(10, 99) for part in ALL_PARTS
}