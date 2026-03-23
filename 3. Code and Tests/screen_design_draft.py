import time
import sys

# defining a slow print for menu
def slow_print(text, speed=0.09):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)  # Controls speed (seconds)
    print() 

# defining a slow input for menu
def slow_input(text, delay=0.05):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)  # Pauses the program for a short duration
    print() 

# Main menu
slow_print("Welcome to Explosive Day!!")
print("_ _ _ _ _ _ _ _ _ _ _ _ _ _")
play = slow_print("1. Play")
instructions = slow_print("2. Instructions")
settings = slow_print("3. Settings")
exit = slow_print("4. Exit")
print("- - - - - - - - - - - - - -")
choice = slow_input("(lowercase) Your choice: ")

# Play choice
if choice == "play":
   slow_print("Nice Choice!")
   print("_ _ _ _ _ _ _ _ _ _ _ _ _ _")
   slow_print("Choose Your Difficulty:")
   easy = slow_print("1. Easy")
   medium = slow_print("2. Medium")
   hard = slow_print("3. Hard")
   back = slow_print("5. Back")
   print("- - - - - - - - - - - - - -")
   difficulty = slow_input("(lowercase) Your choice: _ ")
