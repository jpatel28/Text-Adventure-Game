from dataclasses import dataclass
import random

@dataclass
class GamePrint:
    brightness: int = 100

    def print(self, text: str, end='\n'):
        for char in text:
            if char != ' ' and random.randint(1, 100) <= 100 - self.brightness:
                print('.', end='')
            else:
                print(char, end='')
        print("", end=end)

    def abs_print(self, text: str, end='\n'):
        print(text, end=end)

gamePrint = GamePrint()