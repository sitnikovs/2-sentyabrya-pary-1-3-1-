class Figure:
    def __init__(self, x=0, y=0, color="черный"):
        self.__x = x
        self.__y = y
        self.__color = color
    def get_coords(self):
        return (self.__x, self.__y)
    def set_coords(self, x, y):
        self.__x = x
        self.__y = y
    def get_color(self):
        return self.__color
    def set_color(self, color):
        self.__color = color
    def draw(self):
        print("Рисуется фигура")
    def calculate_area(self):
        return 0
class Circle(Figure):
    def __init__(self, radius, x=0, y=0, color="черный"):
        super().__init__(x, y, color)
        self.__radius = radius
    def get_radius(self):
        return self.__radius
    def set_radius(self, radius):
        self.__radius = radius
    def calculate_area(self):
        return 3.14159 * self.__radius * self.__radius
    def draw(self):
        print(f"Рисуется круг с радиусом {self.__radius}")
class Square(Figure):
    def __init__(self, side, x=0, y=0, color="черный"):
        super().__init__(x, y, color)
        self.__side = side
    def get_side(self):
        return self.__side
    def set_side(self, side):
        self.__side = side
    def calculate_area(self):
        return self.__side * self.__side
    def draw(self):
        print(f"Рисуется квадрат со стороной {self.__side}")

circle1 = Circle(5, 0, 0, "красный")
circle2 = Circle(3, 2, 3, "синий")
square1 = Square(4, -1, 1, "зеленый")
square2 = Square(6, 5, -2, "желтый")
circle3 = Circle(2, -3, 4, "фиолетовый")

figures = [circle1, circle2, square1, square2, circle3]

total_area = 0
for figure in figures:
    total_area += figure.calculate_area()
    figure.draw()

print(f"\nОбщая площадь всех фигур: {total_area:.2f}")