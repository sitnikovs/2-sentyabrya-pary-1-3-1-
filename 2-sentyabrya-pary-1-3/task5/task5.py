class Figure:
    def __init__(self, coords=(0, 0), width=1, color="black"):
        self.coords = coords
        self.width = width
        self.color = color
    def move(self, dx, dy):
        self.coords = (self.coords[0] + dx, self.coords[1] + dy)
    def set_color(self, color):
        self.color = color
class Circle(Figure):
    def __init__(self, radius, coords=(0, 0), width=1, color="black"):
        super().__init__(coords, width, color)
        self.radius = radius
class Rectangle(Figure):
    def __init__(self, height, width, coords=(0, 0), line_width=1, color="black"):
        super().__init__(coords, line_width, color)
        self.height = height
        self.width = width
class Triangle(Figure):
    def __init__(self, side_a, side_b, side_c, coords=(0, 0), width=1, color="black"):
        super().__init__(coords, width, color)
        self.side_a = side_a
        self.side_b = side_b
        self.side_c = side_c

circle = Circle(3, (5, 20), 2, "розовый")
rectangle = Rectangle(4, 6, (0, 0), 3, "синий")
triangle = Triangle(3, 4, 5, (5, 5), 1, "черный")

circle.move(15, -10)
rectangle.set_color("желтый")

print(f"Круг: координаты {circle.coords}, радиус {circle.radius}, цвет {circle.color}")
print(f"Прямоугольник: координаты {rectangle.coords}, высота {rectangle.height}, ширина {rectangle.width}, цвет {rectangle.color}")
print(f"Треугольник: координаты {triangle.coords}, стороны {triangle.side_a}, {triangle.side_b}, {triangle.side_c}, цвет {triangle.color}")