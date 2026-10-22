class Graph:
    def __init__(self, x=0, y=0, scale=1.0):
        self._x = x
        self._y = y
        self._scale = scale
    
    def move(self, dx, dy):
        self._x += dx
        self._y += dy
    
    def change_scale(self, factor):
        self._scale *= factor
    
    def get_state(self):
        return f"Graph(x={self._x}, y={self._y}, scale={self._scale})"

graph1 = Graph(5, 3, 2.0)
graph2 = Graph(-2, 7, 1.5)
graph3 = Graph(10, -4, 0.8)

graph1.move(3, -2)
graph2.change_scale(0.5)

print(graph1.get_state())
print(graph2.get_state())
print(graph3.get_state())