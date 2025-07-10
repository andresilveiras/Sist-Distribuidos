# Códigos de cores ANSI para o terminal
COLOR_GREEN = '\033[92m'
COLOR_YELLOW = '\033[93m'
COLOR_RED = '\033[91m'
COLOR_RESET = '\033[0m' # Reseta a cor para o padrão do terminal
class Buffer:
    """
    Representa um buffer de estoque para uma determinada peça, com lógica de Kanban.
    """
    def __init__(self, part_name: str, max_capacity: int, yellow_level: int, red_level: int):
        """
        Inicializa o buffer.
        Args:
            part_name (str): O nome da peça.
            max_capacity (int): A capacidade máxima do buffer.
            yellow_level (int): O nível que ativa o status AMARELO.
            red_level (int): O nível que ativa o status VERMELHO.
        """
        self.part_name = part_name
        self.max_capacity = max_capacity
        self.yellow_level = yellow_level
        self.red_level = red_level
        # O buffer começa cheio
        self.current_quantity = max_capacity

    @property
    def status(self) -> str:
        """Retorna a cor do status atual do buffer (Kanban)."""
        if self.current_quantity <= self.red_level:
            return "VERMELHO"
        if self.current_quantity <= self.yellow_level:
            return "AMARELO"
        return "VERDE"

    def check_out(self, quantity: int) -> bool:
        """
        Tenta decrementar a quantidade de peças no buffer.
        Retorna True se bem-sucedido, False se não houver estoque suficiente.
        """
        if self.current_quantity >= quantity:
            self.current_quantity -= quantity
            return True
        return False

    def check_in(self, quantity: int):
        """Incrementa a quantidade de peças no buffer."""
        self.current_quantity += quantity
        if self.current_quantity > self.max_capacity:
            self.current_quantity = self.max_capacity

    def __str__(self) -> str:
        """
        Retorna a representação em string do objeto, que será usada pelo print().
        """
        #return f"{self.part_name}: {self.current_quantity}/{self.max_capacity} ({self.status})"
        status_color = COLOR_GREEN
        if self.status == "AMARELO":
            status_color = COLOR_YELLOW
        elif self.status == "VERMELHO":
            status_color = COLOR_RED

        return (f"{self.part_name}: {self.current_quantity}/{self.max_capacity} "
                f"({status_color}{self.status}{COLOR_RESET})")
