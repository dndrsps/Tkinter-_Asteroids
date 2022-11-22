import tkinter as tk
from config import *
from model import *
from objects import *

class Game:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas
        self.create_new_game()
    
    def create_new_game(self) -> None:
        '''Resets all of the game variables, starts a new game'''
        self.player = Player(Vector2D(WIDTH//2, HEIGHT//2), size = PLAYER_SIZE)
        self.asteroids = []
        self.missles = []
        self.animations = []
        self.levels = 0
        self.score = 0
        self.lives = START_LIVES
        self.is_new_wave = True
        self.is_game_over = False
        self.is_paused = False
        self.is_shooting = False
        self.is_accelerating = False
        self.is_turning_left = False
        self.is_turning_right = False

    def loop(self) -> None:
        '''The main gameloop'''
        if self.lives < 0:
            self.is_paused = True
            self.is_game_over = True
        self.level_controller()
        self.canvas.delete("all") 
        self.refresh_asteroids()
        self.refresh_missles()
        self.refresh_player()
        self.refresh_animations()
        self.refresh_HUD()
        if not self.is_paused:
            self.canvas.after(REFRESH_RATE, self.loop)

    def refresh_asteroids(self) -> None:
        for asteroid in self.asteroids:
            self.detect_collision(asteroid)
            asteroid.update()
            if asteroid.is_to_dispose:
                self.asteroids.remove(asteroid)
            else:
                asteroid.draw(self.canvas)

    def refresh_missles(self):
        for missle in self.missles:
            missle.update()
            if missle.is_to_dispose:
                self.missles.remove(missle)
            else:
                missle.draw(self.canvas)

    def refresh_player(self):
        if self.is_shooting:
            self.shoot()
        if self.is_accelerating:
            self.player.accelerate()
        if self.is_turning_left:
            self.player.rotate(TURNING_RATE)
        if self.is_turning_right:
            self.player.rotate(-TURNING_RATE)
        self.player.update()
        self.player.draw(self.canvas)
    
    def refresh_animations(self):
        for animation in self.animations:
            if animation.is_disposable:
                self.animations.remove(animation)
            animation.play(self.canvas)
            
    def detect_collision(self, asteroid: Asteroid) -> None:
        '''Detect collision with Player or missles'''
        if asteroid.is_collide_with(self.player):
            self.player_collision(asteroid)
            return
        for missle in self.missles:
            if asteroid.is_collide_with(missle):
                self.missle_collision(missle, asteroid)  

    def level_controller(self) -> None:
        if self.is_new_wave:
            self.levels += 1
            for i in range(self.levels):
                self.asteroids.append(Asteroid(self.safe_distance_position(100), 
                                        size = ASTEROID_SIZE, 
                                        type = AsteroidType.WHOLE))
            self.is_new_wave = False
        if not self.asteroids and not self.animations:
            self.is_new_wave = True
    
    def safe_distance_position(self, distance: int) -> Vector2D:
        """Returns a random position (Vector2D) outside the given [distance] from the player,
        but inside the window. It's for adding new asteroids to the room.
        """
        position = random_vector(0, WIDTH, 0, HEIGHT)
        while self.player.center.distance(position) < distance:
            position = random_vector(0, WIDTH, 0, HEIGHT)
        return position

    def player_collision(self, asteroid: Asteroid) -> None:
        '''Handles the asteroid's collision with the Player'''
        if self.player.is_invincible:
            return
        self.asteroids += asteroid.destroy()
        self.lives -= 1
        self.player.set_invincible()
        self.animations.append(ExplosionAnimation(asteroid.center, 50))

    def missle_collision(self, missle: Missle, asteroid: Asteroid) -> None:
        '''Handles the asteroid's collision with a missle'''
        if missle.is_to_dispose:
            return
        missle.is_to_dispose = True
        self.asteroids += asteroid.destroy()
        self.score += 1
        self.animations.append(ExplosionAnimation(asteroid.center, 50))

    def refresh_HUD(self):
        self.canvas.create_text(FONT_SIZE*4, FONT_SIZE+2, 
            text=f"LEVEL: {self.levels}", 
            fill=TEXT_COLOR, font=(FONT, FONT_SIZE, FONT_STYLE))
        self.canvas.create_text(WIDTH-(FONT_SIZE*5), FONT_SIZE+2, 
            text=f"SCORE: {self.score:03d}", 
            fill=TEXT_COLOR, font=(FONT, FONT_SIZE, FONT_STYLE))
        self.canvas.create_text(WIDTH//2, FONT_SIZE+2, 
            text=('+'*self.lives), #♡
            fill=TEXT_COLOR, font=(FONT, int(FONT_SIZE*1.5), FONT_STYLE))
        if self.is_game_over:
            self.canvas.create_text(WIDTH//2, HEIGHT//3, 
            text="GAME OVER", 
            fill=TEXT_COLOR, font=(FONT, WIDTH//10, FONT_STYLE))
            self.canvas.create_text(WIDTH//2, HEIGHT//2, 
            text="press <N> for NEW GAME\n "+ "press <Q> to QUIT".center(25), 
            fill=TEXT_COLOR, font=(FONT, FONT_SIZE, FONT_STYLE))

    def shoot(self) -> None:
        if self.player.can_shoot():
            new_missle = self.player.shoot()
            self.missles.append(new_missle)

    def pause(self) -> None:
        if self.is_game_over:
            return
        if self.is_paused:
            self.is_paused = False
            self.loop()
        else:
            self.is_paused = True
    
    def start_new_game(self):
        if not self.is_game_over:
            return
        self.is_game_over = False
        self.create_new_game()
        self.is_paused = False
        self.loop()

class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry('%dx%d+%d+%d' % (WIDTH,
                                       HEIGHT,
                                       (screen_width-WIDTH)//2,
                                       (screen_height-HEIGHT)//2))
        self.resizable(False, False)
        self.canvas = tk.Canvas(self, bg=BG, height=HEIGHT, width=WIDTH)
        self.canvas.pack()
        self.game = Game(self.canvas)
        self.bind('<KeyPress>',self.key_press)
        self.bind('<KeyRelease>',self.key_release)
        self.game.loop()

    def key_press(self, event):
        match event.keysym:
            case 'w'|'Up':
                self.game.is_accelerating = True
            case 'a'|'Left':
                self.game.is_turning_left = True
            case 'd'|'Right':
                self.game.is_turning_right = True
            case 'space':
                self.game.is_shooting = True
            case 'p':
                self.game.pause()
            case 'n':
                self.game.start_new_game()
            case 'q':
                if self.game.is_game_over:
                    self.destroy()

    def key_release(self, event):
        match event.keysym:
            case 'w'|'Up':
                self.game.is_accelerating = False
            case 'a'|'Left':
                self.game.is_turning_left = False
            case 'd'|'Right':
                self.game.is_turning_right = False
            case 'space':
                self.game.is_shooting = False

if __name__ == "__main__":
    app = Window()
    app.mainloop()

 
