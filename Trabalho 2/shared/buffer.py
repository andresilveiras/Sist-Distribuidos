class Buffer:
    def __init__(self, part_name, initial_stock, yellow_limit, red_limit):
        self.part_name = part_name
        self.stock = initial_stock
        self.yellow_limit = yellow_limit
        self.red_limit = red_limit

    def check_in(self, amount):
        self.stock += amount

    def check_out(self, amount):
        self.stock = max(0, self.stock - amount)

    def status(self):
        if self.stock <= self.red_limit:
            return "VERMELHO"
        elif self.stock <= self.yellow_limit:
            return "AMARELO"
        return "VERDE"
