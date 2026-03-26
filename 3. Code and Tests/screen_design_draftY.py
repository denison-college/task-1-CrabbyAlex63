#python -m pip install six
#pip install Gooey
from argparse import ArgumentParser
import sys
import time
from gooey import Gooey, GooeyParser

# This function makes text appear slowly in GUI
def slow_print(text, speed=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    print()

@Gooey(program_name="Explosive Day")
def main():
    
    parser = GooeyParser(description="Welcome to Explosive Day!!")
    
    parser.add_argument(
        'action', 
        metavar='Main Menu',
        choices=['Play', 'Instructions'],
        help='What would you like to do?'
    )
    
    parser.add_argument(
        'difficulty',
        metavar='Difficulty',
        choices=['Easy', 'Medium', 'Hard'],
        help='Choose your challenge level'
    )

    args = parser.parse_args()

    # game logic starts here after the user clicks 'Start'
    slow_print("--- Loading Explosive Day ---")
    
    # Play action
    if args.action == "Play":
        print("Nice Choice!")
        print(f"Starting game on {args.difficulty} mode...")

    # Easy mode
        
    # Instructions action
    if args.action == "Instructions":
        print("Knowledge means survival.\n")
        print("The difficulty you choose will dictate how hard and more bomb-packed the game is. Your goal is to strategically locate and mark all the bombs without setting one off. \n")
        print("Upon your mission, you will come across ‘powers’ which may be beneficial or negative towards your mission. \n")
        print("To win the game, all tiles must be correctly marked or cleared.\n")
        print("To mark a tile of a bomb, you are to type the coordinates of the chosen tile, then when given the selection prompt, you choose ‘Mark’. This will change the tile into a ‘p’, this represents a flag.\n") 
        print("To reveal a tile, you are to type the coordinates of the chosen tile, then when given the selection prompt, you choose ‘Reveal’. This will change the tile to one of the following 2: 0, which represents a clear tile, or an ?, which represents a bomb.\n")
        print("Upon discovering a bomb you will lose the game.\n")
    else:
        print(f"You selected: {args.action}")
 
# Gooey LAUNCHER
if __name__ == '__main__':
    main()