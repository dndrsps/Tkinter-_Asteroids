import tkinter as tk
from config import *
from highscore import HighScoreTable
from model import *
from objects import *
import main
import time


class Screen:
    """Base class for screens of game phases"""
    def __init__(self, window: main.Window) -> None:
        self.app = window
        self.canvas = window.canvas
        self.canvas.focus_set()
        self.canvas.bind("<KeyPress>", self.key_press_command)
        self.canvas.bind("<KeyRelease>", self.key_release_command)
    
    def key_press_command(self, event):
        pass

    def key_release_command(self, event):
        pass

    def loop(self):
        pass


class GameScreen(Screen):
    """The main game object"""
    def __init__(self, window: main.Window) -> None:
        super().__init__(window)
        self.create_new_game()
    
    def create_new_game(self) -> None:
        """Resets all of the game variables, starts a new game"""
        self.canvas.delete("all")
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
        if self.is_game_over:
            end_screen = EndScreen(self.app, self.score)
            self.is_paused = True
            end_screen.loop()
        if self.lives < 0:
            if not self.player.is_destroyed:
                self.animations.append(TextAnimation(Vector2D(WIDTH//2, HEIGHT//4), 280, "GAME OVER", WIDTH//20))
                self.animations.append(PlayerExplosionAnimation(self.player, 280))
                self.animations.append(ExplosionAnimation(self.player.center, 30, PLAYER_COLOR))
                self.player.is_destroyed = True      
            if len(self.animations) == 0:
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
        
    def get_FPS(self) -> str:
        """Calculates Frames per second (FPS) and returns it as a one-decimal-number string"""
        delta_time = time.time()-self.time
        self.time = time.time()
        if delta_time != 0:
            return "{:.1f}".format(1/delta_time)
        return '0.0'

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
        """Starts a new level by adding new asteroids to the room
        when all of the existing ones were destroyed"""
        if self.is_new_wave:
            self.levels += 1
            for i in range(self.levels):
                self.asteroids.append(Asteroid(self.safe_distance_position(100), 
                                        size = ASTEROID_SIZE, 
                                        type = AsteroidType.WHOLE))
            self.animations.append(TextAnimation(Vector2D(WIDTH//2, HEIGHT//3),
                                                 80, f"ROUND {self.levels}", FONT_SIZE*2))
            self.is_new_wave = False
        if not self.asteroids and not self.animations and not self.missles:
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
        if self.player.is_destroyed:
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
        if asteroid.type is AsteroidType.QUARTER and random_bool(HEALTH_DROP_FREQ):
            self.pick_ups.append(HealthPickUp(asteroid.center, 10))
        self.score += 1
        self.animations.append(ExplosionAnimation(asteroid.center, 50))

    def update_HUD(self) -> None:
        """Displays and updates text of levels, scores and lives count on the screen"""
        self.canvas.create_text(FONT_SIZE*4, FONT_SIZE+2, 
            text=f"ROUND: {self.levels}", 
            fill=TEXT_COLOR, font=(FONT, FONT_SIZE, FONT_STYLE))
        
        self.canvas.create_text(WIDTH-(FONT_SIZE*5), FONT_SIZE+2, 
            text=f"SCORE: {self.score:03d}", 
            fill=TEXT_COLOR, font=(FONT, FONT_SIZE, FONT_STYLE))
        
        self.canvas.create_text(WIDTH//2, FONT_SIZE+2, 
            text=('+'*self.lives), #♡
            fill=TEXT_COLOR, font=(FONT, int(FONT_SIZE*1.5), FONT_STYLE))
                    
        if self.is_paused and not self.is_game_over:
            self.canvas.create_text(WIDTH//2, HEIGHT//3, 
                text="||", 
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
    
    def switch_debug(self) -> None:
        if self.is_debug_on:
                self.is_debug_on = False
        else:
            self.is_debug_on = True

    def start_new_game(self):
        """Restarts the game"""
        if not self.is_game_over:
            return
        self.is_game_over = False
        self.create_new_game()
        self.is_paused = False
        self.loop()

    def key_press_command(self, event) -> None:
        match event.keysym:
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
                self.switch_debug()

    def key_release_command(self, event) -> None:
        match event.keysym:
            case 'w'|'Up':
                self.is_accelerating = False
            case 'a'|'Left':
                self.is_turning_left = False
            case 'd'|'Right':
                self.is_turning_right = False
            case 'space':
                self.is_shooting = False


class StartScreen(Screen):
    def __init__(self, window: main.Window) -> None:
        super().__init__(window)
        self.buttons = []
        self.init_buttons()
        self.active_button_index = 0
        self.end = False
    
    def init_buttons(self) -> None:
        button_width = WIDTH//3
        button_height = HEIGHT//10
        spacing = int(button_height*1.5)
        self.buttons.append(Button(self.canvas, Vector2D(WIDTH//2, HEIGHT//2), button_width, button_height, "NEW GAME"))
        self.buttons.append(Button(self.canvas, Vector2D(WIDTH//2, HEIGHT//2+spacing), button_width, button_height, "HIGHSCORES"))
        self.buttons.append(Button(self.canvas, Vector2D(WIDTH//2, HEIGHT//2+(spacing*2)), button_width, button_height, "QUIT"))

    def draw(self) -> None:
        self.canvas.delete("all")
        self.canvas.create_text(WIDTH//2, HEIGHT//4, 
                text=TITLE.upper(), 
                fill=TEXT_COLOR, font=(FONT, WIDTH//12, FONT_STYLE))
        for index, button in enumerate(self.buttons):
            if index == self.active_button_index:
                button.is_active = True
            else:
                button.is_active = False
            button.draw()

    def key_press_command(self, event) -> None:
        match event.keysym:
            case "Down":
                self.active_button_index = (self.active_button_index+1) % len(self.buttons)
            case "Up":
                self.active_button_index -= 1
                if self.active_button_index == -1:
                    self.active_button_index = len(self.buttons)-1
            case "Return":
                self.button_action()
    
    def key_release_command(self, event) -> None:
        pass
    
    def button_action(self) -> None:
        match self.active_button_index:
            case 0:
                self.end = True
                GameScreen(self.app).loop()
            case 1:
                self.end = True
                HighScoresScreen(self.app).loop()
            case 2: 
                self.app.destroy()
    
    def loop(self) -> None:
        if self.end:
            return
        self.draw()
        self.canvas.after(REFRESH_RATE, self.loop)


class HighScoresScreen(Screen):
    def __init__(self, window: main.Window, name: str="default", score: int=0) -> None:
        super().__init__(window)
        self.init_buttons()
        self.end = False
        self.score_table = HighScoreTable("highscores")
        if not name == "default":
            self.score_table.write_entry(name, score)
    
    def init_buttons(self):
        self.buttons = []
        button_width = WIDTH//3
        button_height = HEIGHT//10
        self.buttons.append(Button(self.canvas, Vector2D(WIDTH//2, HEIGHT//7*6), button_width, button_height, "MAIN MENU"))
        self.active_button_index = 0

    def draw(self):
        self.canvas.delete("all")
        self.canvas.create_text(WIDTH//2, HEIGHT//6, 
                text="HIGHSCORES", 
                fill=TEXT_COLOR, font=(FONT, WIDTH//16, FONT_STYLE))
        for index, button in enumerate(self.buttons):
            if index == self.active_button_index:
                button.is_active = True
            else:
                button.is_active = False
            button.draw()
        spacing = HEIGHT//12
        for ind, entry in enumerate(self.score_table.top_scores(5)):
            self.canvas.create_text(WIDTH//2, (HEIGHT//3)+(spacing*ind), 
                text=entry, 
                fill=TEXT_COLOR, font=("Impact", spacing//2, "normal"))
    
    def loop(self):
        if self.end:
            return
        self.draw()
        self.canvas.after(REFRESH_RATE, self.loop)

    def key_press_command(self, event) -> None:
        if event.keysym == "Return":
            self.end = True
            StartScreen(self.app).loop()


class EndScreen(Screen):
    def __init__(self, window: main.Window, score: int) -> None:
        super().__init__(window)
        self.score = score
        self.letter_slots = ["_", "_", "_"] 
        self.active_letter_index = 0
        self.active_button_index = 0
        self.init_buttons()
        self.end = False

    def init_buttons(self) -> None:
        self.buttons = []
        button_width = WIDTH//3
        button_height = HEIGHT//16
        spacing = int(button_height*1.5)
        self.buttons.append(Button(self.canvas, Vector2D(WIDTH//2, HEIGHT//3*2), button_width, button_height, "SUBMIT SCORE"))
        self.buttons.append(Button(self.canvas, Vector2D(WIDTH//2, HEIGHT//3*2+spacing), button_width, button_height, "RESTART"))
        self.buttons.append(Button(self.canvas, Vector2D(WIDTH//2, HEIGHT//3*2+(spacing*2)), button_width, button_height, "MAIN MENU"))

    def loop(self):
        if self.end:
            return
        self.canvas.delete("all")
        self.draw()
        self.canvas.after(REFRESH_RATE, self.loop)

    def draw(self) -> None:       
        self.canvas.delete("all")
        self.canvas.create_text(WIDTH//2, HEIGHT//5, 
                text=f"SCORE: {self.score}", 
                fill=TEXT_COLOR, font=(FONT, WIDTH//20, FONT_STYLE))
        self.canvas.create_text(WIDTH//2, HEIGHT//3, 
                text=f"ENTER YOUR NAME:", 
                fill=TEXT_COLOR, font=(FONT, WIDTH//30, FONT_STYLE))
        for i, letter in enumerate(self.letter_slots):
            self.canvas.create_text(WIDTH//2 + ((i-1)*WIDTH//8), HEIGHT//2, 
                text=letter, 
                fill=TEXT_COLOR, font=(FONT, WIDTH//16, FONT_STYLE))
        for index, button in enumerate(self.buttons):
            if index == self.active_button_index:
                button.is_active = True
            else:
                button.is_active = False
            button.draw()
    
    def key_release_command(self, event):
        match event.keysym:
            case "BackSpace":
                if self.active_letter_index == 0:
                    return
                self.active_letter_index -= 1
                self.letter_slots[self.active_letter_index] = "_"
            case "Down":
                self.active_button_index = (self.active_button_index+1) % len(self.buttons)
            case "Up":
                self.active_button_index -= 1
                if self.active_button_index == -1:
                    self.active_button_index = len(self.buttons)-1
            case "Return":
                self.button_action()
            case other:
                if len(event.keysym) == 1 and event.keysym.isalnum() and self.active_letter_index < 3:
                    self.letter_slots[self.active_letter_index] = event.keysym.upper()
                    self.active_letter_index = self.active_letter_index+1
    
    def button_action(self) -> None:
        match self.active_button_index:
            case 0:
                self.end = True
                HighScoresScreen(self.app, "".join(self.letter_slots), self.score).loop()
            case 1:
                self.end = True
                GameScreen(self.app).loop()
            case 2: 
                self.end = True
                StartScreen(self.app).loop()


class Button:
    def __init__(self, canvas: tk.Canvas, position: Vector2D, width: int, height: int, text: str):
        self.canvas = canvas
        self.center = position
        self.width = width
        self.height = height
        self.text = text
        self.is_active = False

    def draw(self):
        x0, y0 = self.center.x - self.width//2, self.center.y - self.height/2
        x1, y1 = self.center.x + self.width//2, self.center.y + self.height/2
        fill_color = BG
        outline_ = TEXT_COLOR
        text_color = TEXT_COLOR
        if self.is_active:
            fill_color = TEXT_COLOR
            text_color = BG
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill_color, outline=outline_)
        self.canvas.create_text(self.center.x, self.center.y, text=self.text, fill= text_color, font=(FONT, self.height//2, FONT_STYLE))
    

    
