import tkinter as tk
from model import Vector2D, random_num, random_vector
from enum import Enum
from config import*


class AsteroidType(Enum):
    WHOLE = 'whole'
    HALF = 'half'
    QUARTER = 'quarter'


class SpaceObject:
    '''Base class for all space objects'''
    def __init__(self, position: Vector2D, size: int) -> None:
        self.size = size
        self.center = position
        self.shape = []
        self.border_points = []
        self.speed = Vector2D.zero_vector()
        self.heading = 0
        self.init_shape()
        self.update_border_points()
        self.is_to_dispose = False
        self.color = DRAW_COLOR
    
    def __str__(self) -> str:
        return f"{type(self)} x={self.center.x}, y={self.center.y}"
    
    def init_shape(self) -> None:
        pass
    
    def update_border_points(self) -> None:
        self.border_points = []
        for point in self.shape:
            self.border_points.append((self.center + point).rotate(self.heading, self.center))

    def update(self) -> None:
        self.center += self.speed
        self.center.x = self.center.x % WIDTH
        self.center.y = self.center.y % HEIGHT
        self.update_border_points()
        self.is_to_dispose = self.is_disposable()

    def draw(self, canvas: tk.Canvas) -> None:
        
        points =  self.border_points+self.border_points[:1]
        for i in range(len(points)-1):
            x1, y1, x2, y2 = int(points[i].x), int(points[i].y), int(points[i+1].x), int(points[i+1].y)
            canvas.create_line(x1, y1, x2, y2, width=1, fill=self.color)
            
    def rotate(self, degree) -> None:
        self.heading += degree

    def is_disposable(self) -> bool:
        return False


class Player(SpaceObject):
    '''Spaceship of the player'''
    def __init__(self, position: Vector2D, size: int):
        self.exhaust_shape = []
        super().__init__(position, size)
        self.reload_timer = RELOAD_RATE
        self.invincible_timer = 40
        self.is_accelerating = False
        self.is_invincible = False
        self.color = PLAYER_COLOR
        self.animation_timer = 0
        self.update_acceleration()
        self.is_destroyed = False
        
    def init_shape(self) -> None:
        A = Vector2D(0, -self.size)
        B = Vector2D(-self.size//2, + self.size//2)
        C = Vector2D(self.size//2, + self.size//2)
        self.shape.append(A)
        self.shape.append(B)
        self.shape.append(C)

        D = Vector2D(-(self.size//2-2), self.size//2+3)
        E = Vector2D(0, self.size//2+9)
        F = Vector2D((self.size//2-2), self.size//2+3)
        self.exhaust_shape.append(D)
        self.exhaust_shape.append(E)
        self.exhaust_shape.append(F)
    
    def update_border_points(self):
        self.exhaust_points = []
        for point in self.exhaust_shape:
            self.exhaust_points.append((self.center + point).rotate(self.heading, self.center))
        return super().update_border_points()

    def draw_exhaust(self, canvas: tk.Canvas) -> None:
        canvas.create_line(self.exhaust_points[0].x, 
            self.exhaust_points[0].y, 
            self.exhaust_points[1].x, 
            self.exhaust_points[1].y, 
            width=2, fill=DRAW_COLOR)
        canvas.create_line(self.exhaust_points[1].x, 
            self.exhaust_points[1].y, 
            self.exhaust_points[2].x, 
            self.exhaust_points[2].y, 
            width=2, fill=DRAW_COLOR)

    def draw(self, canvas: tk.Canvas):
        if self.is_destroyed:
            return
        if self.is_accelerating:
            self.draw_exhaust(canvas)
            self.is_accelerating = False
        if self.is_invincible:
            #blinking when its invincible
            if (self.animation_timer//2) % 4 == 0:
                super().draw(canvas)
        else:
            super().draw(canvas)

    def update_acceleration(self) -> None:
        self.acceleration = Vector2D(0, -ACCELERATION).rotate(self.heading, Vector2D.zero_vector())

    def accelerate(self) -> None:
        self.update_acceleration()
        self.speed += self.acceleration
        self.is_accelerating = True
    
    def update(self):
        self.reload_timer -= 1
        if self.is_invincible :
            self.invincible_timer -= 1
            self.animation_timer += 1
        if self.invincible_timer < 1:
            self.is_invincible = False
            self.animation_timer = 0
        super().update()

    def can_shoot(self) -> bool:
        if self.is_destroyed:
            return False
        return self.reload_timer < 0

    def shoot(self) -> "Missle":
        self.reload_timer = RELOAD_RATE
        return Missle(self.center, self.heading, self.speed, self.size//3)

    def is_disposable(self):

        return self.is_to_dispose

    def set_invincible(self):
        self.is_invincible = True
        self.invincible_timer = 60


class Missle(SpaceObject):
    '''Missle shot by the player. Destroys asteroids'''
    def __init__(self, position: Vector2D, heading: int, initial_speed: Vector2D, size: int):

        super().__init__(position, size)
        self.heading = heading
        self.speed = Vector2D(0, -MISSLE_SPEED).rotate(self.heading, Vector2D.zero_vector()) + initial_speed

    def init_shape(self) -> None:

        A = Vector2D(0, -self.size//2)
        B = Vector2D(0, +self.size//2)

        self.shape.append(A)
        self.shape.append(B)

    def update(self):
        
         self.center += self.speed
         self.update_border_points()
         self.is_to_dispose = self.is_disposable()

    def is_outside_window(self):

        if WIDTH <= self.center.x or self.center.x <= 0:
            return True
        if HEIGHT <= self.center.y or self.center.y <= 0:
            return True
        return False
        
    def is_disposable(self) -> bool:
        
        return self.is_outside_window()


class Asteroid(SpaceObject):
    '''Asteroids to be destroyed'''
    def __init__(self, position: Vector2D, size: int, type: AsteroidType) -> None:
        self.type = type
        super().__init__(position, size)
        self.spin_speed = random_num(3)
        self.destroyed = False
        match self.type:
            case AsteroidType.WHOLE:
                self.speed = Vector2D(0, ASTEROID_SPEED).rotate(random_num(180), Vector2D.zero_vector())
            case AsteroidType.HALF:
                self.speed = Vector2D(0, ASTEROID_SPEED*2).rotate(random_num(180), Vector2D.zero_vector())
            case AsteroidType.QUARTER:
                self.speed = Vector2D(0, ASTEROID_SPEED*3).rotate(random_num(180), Vector2D.zero_vector())

    def init_shape(self) -> None: 
        self.shape.append( Vector2D(0, -self.size//2 + random_num(self.size//4) ) ) #A
        self.shape.append( Vector2D(self.size//3 + random_num(self.size//4), -self.size//3 + random_num(self.size//4)) ) #B
        self.shape.append( Vector2D(self.size//2 + random_num(self.size//4), 0) )  #C
        self.shape.append( Vector2D(self.size//3 + random_num(self.size//4), self.size//3 + random_num(self.size//4)) ) #D
        self.shape.append( Vector2D(0, self.size//2 + random_num(self.size//4)) ) #E
        self.shape.append( Vector2D(-self.size//3 + random_num(self.size//4), self.size//3 + random_num(self.size//4)) ) #F
        self.shape.append( Vector2D(-self.size//2 + random_num(self.size//4), 0 ) ) #G
        self.shape.append( Vector2D(-self.size//3 + random_num(self.size//4), -self.size//3 + random_num(self.size//4)) ) #H        
    
    def spin(self) -> None:
        self.heading += self.spin_speed

    def update(self) -> None:
        self.spin()
        return super().update()

    def get_avg_diameter(self) -> float:
        '''Returns the average diameter of the asteroid for 
        collision checking operations'''
        distances_from_center = [Vector2D(0,0).distance(point) for point in self.shape]
        return sum(distances_from_center) / len(distances_from_center)

    def is_point_inside(self, point: Vector2D) -> bool:
        '''Returns True if the given [point] is inside the average diameter
        of the asteroid. It's for collision checking.'''
        if self.center.distance(point) < self.get_avg_diameter():
            return True
        return False

    def is_collide_with(self, other: SpaceObject) -> bool:
        '''Checks if the [other] object is collide with the asteroid'''
        if self.is_point_inside(other.center):
            return True
        for point in other.border_points:
            if self.is_point_inside(point):
                return True
        return False

    def destroy(self)-> list['Asteroid']:
        '''Destroys the asteroid and returns children'''
        self.destroyed = True
        match self.type:
            case AsteroidType.WHOLE:
                return [Asteroid(self.center, int(self.size*0.75), AsteroidType.HALF),
                        Asteroid(self.center, int(self.size*0.75), AsteroidType.HALF)]
            case AsteroidType.HALF:
                return [Asteroid(self.center, int(self.size*0.6), AsteroidType.QUARTER),
                        Asteroid(self.center, int(self.size*0.6), AsteroidType.QUARTER)]
            case AsteroidType.QUARTER:
                return []

    def is_disposable(self) -> bool:
        return self.destroyed


class HealthPickUp(SpaceObject):
    """Helth pick-up object, dropped by destroyed asteroids"""
    def __init__(self, position, size) -> None:

        super().__init__(position, size)
        self.spin_speed = 5
        self.color = "red"
        self.duration = 350

    def init_shape(self) -> None: 
        self.shape.append(Vector2D(0, -self.size//2))
        self.shape.append(Vector2D(self.size//2, 0))
        self.shape.append(Vector2D(0, self.size//2))
        self.shape.append(Vector2D(-self.size//2, 0))


    def update(self) -> None:
        self.heading += self.spin_speed
        return super().update()

    def is_disposable(self):
        self.duration -= 1
        if self.duration < 1:
            self.is_to_dispose = True
        return self.is_to_dispose

    def is_collide_with(self, player: "Player") -> bool:
        if self.center.distance(player.center) <= self.size:
            return True
        for point in player.border_points:
            if self.center.distance(point) <= self.size:
                return True
        return False
    
        
class Spark:
    '''Randomly flying pixel for explosion animation'''
    def __init__(self, position: Vector2D, color = DRAW_COLOR) -> None:

        self.position = position
        self.speed = random_vector(0, 0, 1, 5).rotate(random_num(180), Vector2D.zero_vector())
        self.color = color
    
    def draw(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(self.position.x-1,
                                self.position.y-1,
                                self.position.x+1,
                                self.position.y+1,
                                fill=self.color)
    def update(self, canvas: tk.Canvas) -> None:
        self.position += self.speed
        self.draw(canvas)


class SpinningLine:
    """Randomly flying and spinnig line segment to animate player's spaceship explosion"""
    def __init__(self, start_point: Vector2D, end_point: Vector2D, color = DRAW_COLOR) -> None:
        self.start_point = start_point
        self.end_point = end_point
        self.speed = Vector2D(0, 0.5).rotate(random_num(180), Vector2D.zero_vector())
        self.color = color
        self.spin_degree = random_num(5)

    def draw(self, canvas: tk.Canvas) -> None:
        canvas.create_line(self.start_point.x, self.start_point.y,
                            self.end_point.x, self.end_point.y,
                            fill=self.color)
    
    def update(self, canvas: tk.Canvas) -> None:
        midpoint = Vector2D.get_midpoint(self.start_point, self.end_point) + self.speed
        self.start_point = (self.start_point+self.speed).rotate(self.spin_degree, midpoint)
        self.end_point = (self.end_point+self.speed).rotate(self.spin_degree, midpoint)
        self.draw(canvas)


class ExplosionAnimation:
    def __init__(self, position: Vector2D, duration: int, color=DRAW_COLOR) -> None:
        
        self.position = position
        self.sparks = [Spark(self.position, color) for i in range(40)]
        self.duration = duration
        self.is_disposable = False
    
    def play(self, canvas: tk.Canvas):
        if self.duration < 1:
            self.is_disposable = True
            return
        for spark in self.sparks:
            spark.update(canvas)
        self.duration -= 1


class PlayerExplosionAnimation:
    def __init__(self, player: Player, duration_frames: int) -> None:
        self.init_segments(player)
        self.duration_frames = duration_frames
        self.is_disposable = False

    def init_segments(self, player: Player) -> None:
        self.segments = []
        self.segments.append(SpinningLine(player.border_points[0], player.border_points[1], player.color))
        self.segments.append(SpinningLine(player.border_points[1], player.border_points[2], player.color))
        self.segments.append(SpinningLine(player.border_points[2], player.border_points[0], player.color))

    def play(self, canvas: tk.Canvas) -> None:
        if self.duration_frames < 1:
            self.is_disposable = True
            return
        for segment in self.segments:
            segment.update(canvas)
        self.duration_frames -= 1


class TextAnimation:
    def __init__(self, position: Vector2D, duration: int, text: str, size: int = FONT_SIZE, color = TEXT_COLOR) -> None:
        self.position = position
        self.text = text
        self.size = size
        self.total_duration = duration
        self.duration = duration
        self.is_disposable = False
        self.color = color
    def play(self, canvas: tk.Canvas):
        if self.total_duration == self.duration:    # the animation not displayed in the first frame
            self.duration -= 1
            return
        if self.duration < 1:
            self.is_disposable = True
            return
        canvas.create_text(self.position.x, self.position.y, 
            text=self.text, 
            fill=self.color, font=(FONT, self.size, FONT_STYLE))
        self.duration -= 1
        
        