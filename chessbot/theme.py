from color import *

class Theme:
    def __init__(self):
        self.move_sound = "assets/sounds/move.wav"
        self.capture_sound = "assets/sounds/capture.wav"
        
    def get_move_sound(self):
        return self.move_sound
    
    def get_capture_sound(self):
        return self.capture_sound 