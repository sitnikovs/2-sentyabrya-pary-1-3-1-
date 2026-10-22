class Cart:
    def __init__(self):
        self.goods = []
    
    def add(self, gd):
        self.goods.append(gd)
    
    def remove(self, indx):
        if 0 <= indx < len(self.goods):
            self.goods.pop(indx)
    
    def get_list(self):
        return [f"{item.name}: {item.price}" for item in self.goods]

class Table:
    def __init__(self, name, price):
        self.name = name
        self.price = price

class TV:
    def __init__(self, name, price):
        self.name = name
        self.price = price

class Notebook:
    def __init__(self, name, price):
        self.name = name
        self.price = price

class Cup:
    def __init__(self, name, price):
        self.name = name
        self.price = price

cart = Cart()
cart.add(TV("Samsung", 50000))
cart.add(TV("LG", 45000))
cart.add(Table("IKEA", 15000))
cart.add(Notebook("Dell", 80000))
cart.add(Notebook("HP", 75000))
cart.add(Cup("ВКУСНОИТОЧКА", 1))