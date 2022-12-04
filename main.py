import tkinter as tk
from config import *
from screens import *

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
        self.start_screen = StartScreen(self)
        self.start_screen.loop()


if __name__ == "__main__":
    app = Window()
    app.mainloop()