class Car:
    def __init__(self):
        self._engine_temperature = 20
    
    def start_engine(self):
        self._engine_temperature = 90
        print("Двигатель прогрет")
    
    def drive(self):
        if self._engine_temperature >= 90:
            print("Поехали!")
        else:
            print("Двигатель не прогрет")

car = Car()

print("Попытка поехать без прогрева:")
car.drive()

print("\nПрямой доступ к температуре:")
print(f"Температура двигателя: {car._engine_temperature}")

print("\nПопытка изменить температуру напрямую:")
car._engine_temperature = 100
print(f"Температура изменена на: {car._engine_temperature}")
car.drive()

print("\nЗапуск двигателя:")
car.start_engine()
car.drive()