class Cat:
    def __init__(self, breed, name, age):
        self.breed = breed
        self.name = name
        self.age = age
    def __str__(self):
        return f"Кот: {self.name} | Порода: {self.breed} | Возраст: {self.age} лет"
    def __repr__(self):
        return f"Cat(breed='{self.breed}', name='{self.name}', age={self.age})"

cat1 = Cat("Британская вислоухая", "Пиксель", 3)
cat2 = Cat("Сиамская", "Люся", 2)
cat3 = Cat("Мейн-кун", "Тигр", 5)

print("Информация о котах:")
print("-" * 40)
print(cat1)
print(cat2)
print(cat3)