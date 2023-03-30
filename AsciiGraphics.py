from msvcrt import getch
import msvcrt
import os
import pickle
import random
import time
import colorama
import sys
import socket
import json


colorama.init()

class KeyPressContainer:
    def __init__(self):
        self.pressed_keys = set()

    def add_key(self, key):
        self.pressed_keys.add(key)

    def remove_key(self, key):
        self.pressed_keys.discard(key)

    def is_pressed(self, key):
        return key in self.pressed_keys

    def handle_user_input(self):
        if msvcrt.kbhit():
            char = msvcrt.getch().decode('utf-8')
            if char == 'w':
                self.add_key('w')
            elif char == 's':
                self.add_key('s')
            elif char == 'a':
                self.add_key('a')
            elif char == 'd':
                self.add_key('d')
            elif char == ' ':
                self.add_key('space')
            elif char == 'q':
                sys.exit(0)
        else:
            self.remove_key('w')
            self.remove_key('s')
            self.remove_key('a')
            self.remove_key('d')
            self.remove_key('space')

# Define the size of the game canvas
CANVAS_WIDTH = 40
CANVAS_HEIGHT = 20

# Define the game objects
class GameObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Tank(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 3
        self.direction = 'up'
        self.color = 'green'
        self.symbol = '^'

    def move(self, dx, dy, obstacles):
        new_x = self.x + dx
        new_y = self.y + dy
        if not self._is_in_bounds(new_x, new_y):
            return
        if self._collides_with_obstacle(new_x, new_y, obstacles):
            return
        self.x = new_x
        self.y = new_y
        if dy == -1:
            self.direction = 'up'
        elif dy == 1:
            self.direction = 'down'    
        elif dx == -1:
            self.direction = 'left'    
        elif dx == 1:
            self.direction = 'right'

    def _is_in_bounds(self, x, y):
        return 0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT

    def _collides_with_obstacle(self, x, y, obstacles):
        for obstacle in obstacles:
            if (x, y) in obstacle.get_points():
                return True
        return False
    
    def get_points(self):
        return [(self.x, self.y)]

class Wall(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = 'LIGHTBLACK_EX'
        self.symbol = '#'

    def get_points(self):
        return [(self.x, self.y)]

class Bullet(GameObject):
    def __init__(self, x, y, direction):
        super().__init__(x, y)
        self.direction = direction
        self.color = 'yellow'
        self.symbol = '*'

    def move(self, obstacles):
        dx, dy = self._get_delta()
        new_x = self.x + dx
        new_y = self.y + dy
        if not self._is_in_bounds(new_x, new_y):
            return False
        if self._collides_with_obstacle(new_x, new_y, obstacles):
            return False
        self.x = new_x
        self.y = new_y
        return True

    def _get_delta(self):
        if self.direction == 'up':
            return 0, -1
        elif self.direction == 'down':
            return 0, 1
        elif self.direction == 'left':
            return -1, 0
        elif self.direction == 'right':
            return 1, 0

    def _is_in_bounds(self, x, y):
        return 0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT

    def _collides_with_obstacle(self, x, y, obstacles):
        for obstacle in obstacles:
            if (x, y) in obstacle.get_points():
                return True
        return False
    
    def get_points(self):
        return [(self.x, self.y)]

# Define the game mechanics
class Game:
    HOST = '127.0.0.1'
    PORT = 73631

    def __init__(self):
        self.enemy_tanks = []
        self.obstacles = []
        self.bullets = []
        self.keys_pressed_per_player = {
            "playerA": KeyPressContainer(),
            "playerB": KeyPressContainer(),
        }
        self.players = {
        'playerA': {'w': (0, -1), 's': (0, 1), 'a': (-1, 0), 'd': (1, 0), 'space': (0, 0)},
        'playerB': {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0), 'space': (0, 0)}
}

    def add_enemy_tank(self, x, y):
        tank = Tank(x, y)
        tank.color = 'red'
        tank.symbol = 'V'
        self.enemy_tanks.append(tank)

    def add_playerA_tank(self, x, y):
        self.playerA = Tank(x, y)
    
    def add_playerB_tank(self, x, y):
        self.playerB = Tank(x, y)
        self.playerB.color = 'blue'

    def add_wall(self, x, y):
        wall = Wall(x, y)
        self.obstacles.append(wall)

    def update(self, keys_pressed_per_player):
        self._handle_all_players_input(keys_pressed_per_player)
        self._handle_enemy_ai()
        self._handle_bullets()

    def _handle_all_players_input(self, keys_pressed_per_player):
        # Loop over the players and their movement keys
        for player_name, keys in self.players.items():
            player = getattr(self, player_name)  # Get the player object using its name
            for key, direction in keys.items():
                if self.keys_pressed_per_player[player_name].is_pressed(key):
                    if key == 'space':
                        bullet = Bullet(player.x, player.y, player.direction)
                        self.bullets.append(bullet)
                    else:
                        player.move(*direction, self.obstacles)
    
    def _get_player_by_name(self, player_name):
        if (player_name == "playerA"):
            return self.playerA
        if (player_name == "playerB"):
            return self.playerB
        print("Error! Unknown player name!")
        return None
    
    def _handle_players_input(self, player, keys_pressed):
        dx, dy = 0, 0
        if keys_pressed.is_pressed('w'):
            dy = -1
        elif keys_pressed.is_pressed('s'):
            dy = 1
        elif keys_pressed.is_pressed('a'):
            dx = -1
        elif keys_pressed.is_pressed('d'):
            dx = 1
        player.move(dx, dy, self.obstacles)

        if keys_pressed.is_pressed('space'):
            bullet = Bullet(player.x, player.y, player.direction)
            self.bullets.append(bullet)

    def _handle_enemy_ai(self):
        for tank in self.enemy_tanks:
            direction = random.choice(['up', 'down', 'left', 'right'])
            dx, dy = 0, 0
            if direction == 'up':
                dy = -1
            elif direction == 'down':
                dy = 1
            elif direction == 'left':
                dx = -1
            elif direction == 'right':
                dx = 1
            tank.move(dx, dy, self.obstacles)

            if random.random() < 0.1:
                bullet = Bullet(tank.x, tank.y, tank.direction)
                self.bullets.append(bullet)

    def _handle_bullets(self):
        new_bullets = []
        for bullet in self.bullets:
            if bullet.move(self.obstacles):
                new_bullets.append(bullet)
            else:
                # The bullet hit an obstacle or went out of bounds
                pass
        self.bullets = new_bullets

    def draw(self, canvas):
        # Clear the canvas
        canvas.clear()

        # Draw the obstacles
        for obstacle in self.obstacles:
            canvas.draw_sprite(obstacle)

        # Draw the enemy tanks
        for tank in self.enemy_tanks:
            canvas.draw_sprite(tank)

        canvas.draw_sprite(self.playerB)
        # Draw the player
        canvas.draw_sprite(self.playerA)
        # Draw the bullets
        for bullet in self.bullets:
            canvas.draw_sprite(bullet)

class AsciiGraphics:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = [[' ' for _ in range(width)] for _ in range(height)]

    def clear(self):
        self.canvas = [[' ' for _ in range(self.width)] for _ in range(self.height)]

    def draw_sprite(self, sprite):
        symbol = sprite.symbol
        color = sprite.color
        if isinstance(sprite, Tank):
            direction = sprite.direction
            if direction == 'up':
                symbol = '^'
            elif direction == 'down':
                symbol = 'V'
            elif direction == 'left':
                symbol = '<'
            elif direction == 'right':
                symbol = '>'
        for x, y in sprite.get_points():
            px = x
            py = y
            if 0 <= px < self.width and 0 <= py < self.height:
                if color is not None:
                    color_code = getattr(colorama.Fore, color.upper())
                    self.canvas[py][px] = f'{color_code}{symbol}{colorama.Style.RESET_ALL}'
                else:
                    self.canvas[py][px] = symbol

    def render(self):
        display_text = ""
        for row in self.canvas:
            display_text += ''.join(row) + "\n"
        # detect the operating system
        if os.name == 'nt':  # for Windows
            os.system('cls')
        else:  # for Unix-like systems
            os.system('clear')
        print(display_text)


   
def GameStart():
    # Define the level layout
    level = [
        "WWWWWWWWWWWWWWWWWWWWWW",
        "W   W E     W     W W",
        "W W W W WWW W WWW W W",
        "W W W W     W     W W",
        "W W W W WWW WWWWWWW W",
        "W W W W     W     W W",
        "W W W W WWW W WWW W W",
        "W W W W     W     W W",
        "W W W WWWWWWW WWW W W",
        "W W   E     W     W W",
        "W WWWWW WWW W WWW W W",
        "W A     W   W     W W",
        "WWWWWWW WWW WWWWWWW W",
        "W B     W     E   W W",
        "W WWWWWWWWWWWWWWWWWWW",
    ]
    localPlayerA = True
    local_player = "playerA"
    # Create the game and add the sprites
    game = Game()

    # Add the level layout to the game
    for y, row in enumerate(level):
        for x, cell in enumerate(row):
            if cell == "W":
                game.add_wall(x, y)
            elif cell == "E":
                game.add_enemy_tank(x, y)
            elif cell == "A":
                game.add_playerA_tank(x, y)
            elif cell == "B":
                game.add_playerB_tank(x, y)


    canvas = AsciiGraphics(CANVAS_WIDTH, CANVAS_HEIGHT)


    while True:
        # Clear the game screen
        #game.clear_screen()
        keys_pressed_per_player = { "playerA" : KeyPressContainer(), "playerB" : KeyPressContainer() }

        if localPlayerA:  
            keys_pressed = game.keys_pressed_per_player[local_player]
            keys_pressed.handle_user_input()

        # Update the game state
        game.update(keys_pressed_per_player)

        # Draw the game on the canvas
        game.draw(canvas)

        # Render the canvas on the screen
        canvas.render()

        # Sleep for a short time to control the frame rate
        time.sleep(0.05)


class GameServer:
    def __init__(self, host='', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_sockets = []
    
    def start(self):
        # Create a server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)
        print(f"Server started on {self.host}:{self.port}")
        
        # Accept connections from two clients
        while len(self.client_sockets) < 2:
            client_socket, address = self.server_socket.accept()
            print(f"Accepted connection from {address}")
            self.client_sockets.append(client_socket)
        
        # Start the game loop
        self.game_loop()
    
    def game_loop(self):
        # Implement the game logic here
        pass
    
    def close(self):
        # Close all client sockets and the server socket
        for client_socket in self.client_sockets:
            client_socket.close()
        self.server_socket.close()
        print("Server closed")

class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.socket.connect((self.server_ip, self.server_port))
            print("Connected to the server!")
        except Exception as e:
            print(f"Error: {str(e)}")

    def send_message(self, message):
        try:
            self.socket.sendall(message.encode())
        except Exception as e:
            print(f"Error: {str(e)}")

    def receive_message(self):
        try:
            message = self.socket.recv(1024)
            return message.decode()
        except Exception as e:
            print(f"Error: {str(e)}")


def main():
    user_choice = input("Do you want to start a client or server? (Enter 'C' for client, 'S' for server): ")

    if user_choice.upper() == 'C':
        start_client()
    elif user_choice.upper() == 'S':
        start_server()
    else:
        print("Invalid choice. Please enter 'C' or 'S'.")
        main()

def start_client():
    client = Client("localhost", 34334)
    client.connect()

    # Send a message to the server
    client.send_message("Hello, server!")

    # Receive a message from the server
    message = client.receive_message()
    print(message)

def start_server():
    SERVER_HOST = 'localhost'
    SERVER_PORT = 34334

    # create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind the socket to a specific address and port
    server_socket.bind((SERVER_HOST, SERVER_PORT))

    # start listening for incoming connections
    server_socket.listen()

    # create a GameServer object and pass in the socket object
    game_server = GameServer(server_socket)

    # start accepting client connections
    game_server.start()
    game_server.close()

if __name__ == '__main__':
    main()
