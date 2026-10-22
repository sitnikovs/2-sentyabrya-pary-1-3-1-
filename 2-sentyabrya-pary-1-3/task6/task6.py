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
class Line(Figure):
    def __init__(self, length, coords=(0, 0), width=1, color="черный"):
        super().__init__(coords, width, color)
        self.length = length
    def display(self):
        return f"Линия: длина {self.length}, {super().display()}"
class Rect(Figure):
    def __init__(self, height, width, coords=(0, 0), line_width=1, color="черный"):
        super().__init__(coords, line_width, color)
        self.height = height
        self.width = width
    def display(self):
        return f"Прямоугольник: высота {self.height}, ширина {self.width}, {super().display()}"
class Ellipse(Figure):
    def __init__(self, radius, coords=(0, 0), width=1, color="черный"):
        super().__init__(coords, width, color)
        self.radius = radius
    
    def display(self):
        return f"Эллипс: радиус {self.radius}, {super().display()}"

line = Line(10, (5, 5), 2, "красный")
rect = Rect(4, 6, (-3, 2), 3, "фиолетовый")
ellipse = Ellipse(8, (0, -5), 1, "синий")

print(line.display())
print(rect.display())
print(ellipse.display())