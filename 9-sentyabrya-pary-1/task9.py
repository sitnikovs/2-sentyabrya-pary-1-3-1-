# Базовый класс Figure
class Figure:
    def __init__(self, coords, width, color):
        self.coords = coords
        self.width = width
        self.color = color
    
    def draw(self):
        print("Рисуется фигура")

class Line(Figure):
    def draw(self):
        print("Рисуется линия")


class Rect(Figure):
    def draw(self):
        print("Рисуется прямоугольник")


class Ellipse(Figure):
    def draw(self):
        print("Рисуется эллипс")


class Triangle(Figure):
    def draw(self):
        print("Рисуется треугольник")

figures = [
    Line((0, 0, 10, 10), 2, "red"),
    Rect((5, 5, 20, 15), 3, "blue"),
    Ellipse((10, 10, 30, 20), 1, "green")
]

for fig in figures:
    fig.draw()

figures.append(Triangle((15, 15, 25, 25), 2, "yellow"))

print("")
for fig in figures:
    fig.draw()