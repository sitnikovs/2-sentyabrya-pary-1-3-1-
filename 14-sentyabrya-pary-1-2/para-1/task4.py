class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def clone(self):
        return (self.x, self.y)

pt = Point(2, 5)
pt_clone = pt

print(pt.x, pt.y)
print(pt_clone.x, pt_clone.y)