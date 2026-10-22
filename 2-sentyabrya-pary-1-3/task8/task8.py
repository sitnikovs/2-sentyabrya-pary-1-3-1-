class Figure:
    def __init__(self, coords=(0, 0), width=1, color="черный"):
        self.coords = coords
        self.width = width
        self.color = color
    def move(self, dx, dy):
        self.coords = (self.coords[0] + dx, self.coords[1] + dy)
    def set_color(self, color):
        self.color = color
    def display(self):
        return f"координаты {self.coords}, толщина {self.width}, цвет {self.color}"
    def draw(self):
        print("Рисуется фигура")
class Line(Figure):
    def __init__(self, length, coords=(0, 0), width=1, color="черный"):
        super().__init__(coords, width, color)
        self.length = length
    def display(self):
        return f"Линия: длина {self.length}, {super().display()}"
    def draw(self):
        print("Рисуется линия")
class Rect(Figure):
    def __init__(self, height, width, coords=(0, 0), line_width=1, color="черный"):
        super().__init__(coords, line_width, color)
        self.height = height
        self.width = width
    def display(self):
        return f"Прямоугольник: высота {self.height}, ширина {self.width}, {super().display()}"
    def draw(self):
        print("Рисуется прямоугольник")
class Ellipse(Figure):
    def __init__(self, radius, coords=(0, 0), width=1, color="черный"):
        super().__init__(coords, width, color)
        self.radius = radius
    def display(self):
        return f"Эллипс: радиус {self.radius}, {super().display()}"
    def draw(self):
        print("Рисуется эллипс")
class Triangle(Figure):
    def __init__(self, side_a, side_b, side_c, coords=(0, 0), width=1, color="черный"):
        super().__init__(coords, width, color)
        self.side_a = side_a
        self.side_b = side_b
        self.side_c = side_c
    def display(self):
        return f"Треугольник: стороны {self.side_a}, {self.side_b}, {self.side_c}, {super().display()}"
    def draw(self):
        print("Рисуется треугольник")

line = Line(10, (5, 5), 2, "красный")
rect = Rect(4, 6, (-3, 2), 3, "синий")
ellipse = Ellipse(8, (0, -5), 1, "зеленый")
triangle = Triangle(3, 4, 5, (1, 1), 2, "желтый")

figures = [line, rect, ellipse, triangle]

for figure in figures:
    figure.draw()