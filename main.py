import tkinter as tk
from config import *
from model import *
from objects import *
import time


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
        self.pick_ups = []
        self.levels = START_LEVEL
        self.score = 0
        self.lives = START_LIVES
        self.is_new_wave = True
        self.is_game_over = False
        self.is_paused = True
        self.is_shooting = False
        self.is_accelerating = False
        self.is_turning_left = False
        self.is_turning_right = False
        self.is_debug_on = False
        self.time = time.time()

    def loop(self) -> None:
        '''The main gameloop'''
        if self.lives < 0:
            self.is_paused = True
            self.is_game_over = True
        self.level_controller()
        self.canvas.delete("all") 
        self.update_asteroids()
        self.update_missles()
        self.update_pick_ups()
        self.update_player()
        self.update_animations()
        self.update_HUD()
        if not self.is_paused:
            self.canvas.after(REFRESH_RATE, self.loop)
        
    def get_FPS(self):
        delta_time = time.time()-self.time
        self.time = time.time()
        if delta_time != 0:
            return "{:.1f}".format(1/delta_time)
        return 0.0

    def update_asteroids(self) -> None:
        for asteroid in self.asteroids:
            self.detect_collision(asteroid)
            asteroid.update()
            if asteroid.is_to_dispose:
                self.asteroids.remove(asteroid)
                del asteroid
            else:
                asteroid.draw(self.canvas)

    def update_missles(self):
        for missle in self.missles:
            if missle.is_to_dispose:
                self.missles.remove(missle)
            else:
                missle.update()
                missle.draw(self.canvas)

    def update_player(self):
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
    
    def update_animations(self):
        for animation in self.animations:
            if animation.is_disposable:
                self.animations.remove(animation)
                del animation
            else:
                animation.play(self.canvas)

    def update_pick_ups(self):
        for pick_up in self.pick_ups:
            if pick_up.is_collide_with(self.player):
                pick_up.is_to_dispose = True
                self.lives += 1
                self.animations.append(TextAnimation(Vector2D(pick_up.center.x,pick_up.center.y),
                                                 40, "+1", FONT_SIZE, color='red'))
                
            if pick_up.is_to_dispose:
                self.pick_ups.remove(pick_up)
            else:
                pick_up.update()
                pick_up.draw(self.canvas)
            
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
            self.animations.append(TextAnimation(Vector2D(WIDTH//2, HEIGHT//3),
                                                 80, f"LEVEL {self.levels}", FONT_SIZE*2))
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
        """Handles the asteroid's collision with the Player"""
        if self.player.is_invincible:
            return
        self.asteroids += asteroid.destroy()
        self.lives -= 1
        self.player.set_invincible()
        self.animations.append(ExplosionAnimation(asteroid.center, 50))

    def missle_collision(self, missle: Missle, asteroid: Asteroid) -> None:
        """Handles the asteroid's collision with a missle"""
        if missle.is_to_dispose:
            return
        missle.is_to_dispose = True
        self.asteroids += asteroid.destroy()
        if asteroid.type is AsteroidType.QUARTER and random_bool(10):
            self.pick_ups.append(HealthPickUp(asteroid.center, 10))
        self.score += 1
        self.animations.append(ExplosionAnimation(asteroid.center, 50))

    def update_HUD(self) -> None:
        """Displays and updates text of levels, scores and lives count on the screen"""
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
            
            self.canvas.create_text(WIDTH//2, HEIGHT//4*3, 
                text="press <N> for NEW GAME\n "+ "press <Q> to QUIT".center(25), 
                fill=TEXT_COLOR, font=(FONT, FONT_SIZE, FONT_STYLE))
            
        if self.is_paused and not self.is_game_over:
            self.canvas.create_text(WIDTH//2, HEIGHT//3, 
                text=TITLE.upper(), 
                fill=TEXT_COLOR, font=(FONT, WIDTH//10, FONT_STYLE))
            
            self.canvas.create_text(WIDTH//2, HEIGHT*0.75, 
                text=INSTRUCTIONS, 
                fill=TEXT_COLOR, font=(FONT, FONT_SIZE, FONT_STYLE))
            
        if self.is_debug_on:
            self.draw_debug_overlay()

    def draw_debug_overlay(self) -> None:
        """Displays and updates text of FPS count 
        (and maybe later other informations) on the screen"""
        obj_count = len(self.asteroids) + len(self.missles) + len(self.animations)
        self.canvas.create_text(FONT_SIZE*4, HEIGHT-(FONT_SIZE+2), 
            text=f"FPS: {self.get_FPS()}", 
            fill=TEXT_COLOR, font=(FONT, FONT_SIZE, FONT_STYLE))

    def shoot(self) -> None:
        if self.player.can_shoot():
            new_missle = self.player.shoot()
            self.missles.append(new_missle)
      
    def pause(self) -> None:
        """Pauses or upauses the game"""
        if self.is_game_over:
            return
        if self.is_paused:
            self.is_paused = False
            self.loop()
        else:
            self.is_paused = True
    
    def start_new_game(self):
        """Restarts the game"""
        if not self.is_game_over:
            return
        self.is_game_over = False
        self.create_new_game()
        self.is_paused = False
        self.loop()

    def key_press_command(self, key: str) -> None:
        match key:
            case 'w'|'Up':
                self.is_accelerating = True
            case 'a'|'Left':
                self.is_turning_left = True
            case 'd'|'Right':
                self.is_turning_right = True
            case 'space':
                self.is_shooting = True
            case 'p':
                self.pause()
            case 'n':
                self.start_new_game()
            case "F12":
                if self.is_debug_on:
                    self.is_debug_on = False
                else:
                    self.is_debug_on = True

    def key_release_command(self, key: str) -> None:
        match key:
            case 'w'|'Up':
                self.is_accelerating = False
            case 'a'|'Left':
                self.is_turning_left = False
            case 'd'|'Right':
                self.is_turning_right = False
            case 'space':
                self.is_shooting = False
        

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
        if event.keysym == 'q' and self.game.is_game_over:
            self.destroy()
        self.game.key_press_command(event.keysym)

    def key_release(self, event):
        self.game.key_release_command(event.keysym)


if __name__ == "__main__":
    app = Window()
    app.mainloop()

 
