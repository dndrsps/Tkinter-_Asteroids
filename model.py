import math
import random


class Vector2D:

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Vector2D(x={self.x}, y={self.y})"

    def __add__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x + other.x,
                      self.y + other.y)

    def __sub__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x - other.x,
                      self.y - other.y)

    def __abs__(self) -> float:
        return math.sqrt(self.x**2 + self.y**2)

    def __eq__(self, other: "Vector2D") -> bool:
        return self.x == other.x and self.y == other.y

    def rotate(self, degree: int,  axis_point: "Vector2D") -> "Vector2D":
        '''Rotates the vector around the [axis_point] with the given [degree]'''
        radians = math.radians(degree)
        x = self.x - axis_point.x
        y = self.y - axis_point.y
        new_x = x*math.cos(radians) + y*math.sin(radians) + axis_point.x
        new_y = -x*math.sin(radians) + y*math.cos(radians) + axis_point.y
        return Vector2D(new_x, new_y)

    def distance(self, other: "Vector2D") -> float:
        '''Returns the distance between two vectors'''
        return abs(self - other)

    @classmethod
    def zero_vector(cls) -> "Vector2D":
        return Vector2D(0, 0)


def random_vector(min_x: int, max_x: int, min_y: int, max_y: int) -> Vector2D:

    x = random.randint(min_x, max_x)
    y = random.randint(min_y, max_y)

    return Vector2D(x, y)


def random_num(range_num: int) -> int:

    return random.randint(-range_num, range_num)


def random_bool(chance: int) -> bool:
    """Returns True in 1 in [chance] occasion"""
    return random.randint(1, chance) == 1
    




