# install these libraries
import pygame
import random
import math

# initialise a pygame instance
pygame.init()

# pygame screen elements
WIDTH, HEIGHT = 800, 800 # default 800,800
TILE_SIZE = 10
GRID_WIDTH = WIDTH // TILE_SIZE
GRID_HEIGHT = HEIGHT // TILE_SIZE
FPS = 10 # clock ticks {FPS} times a real second

# simple RGB colours
BLACK = (0, 0, 0, 128)
GREY = (128, 128, 128, 0)
YELLOW = (255, 255, 0, 0)
WHITE = (255, 255, 255, 0)
RED = (255, 0, 0, 255)
GREEN = (0, 255, 0, 0)
BLUE = (0, 0, 255, 255)
PURPLE = (255, 0, 255, 0)
CYAN = (0, 255, 255, 0)
BLACK = (0, 0, 0, 0)

# ---- ---- ---- ---- bacteria class ---- ---- ---- ----
class Bacteria:

    # BACTERIA SIMULATION PARAMS; access in class functions as Bacteria.----
    EXISTING_IDS = set()  # store generated IDs, ensuring they dont repeat
    START_POWER = 12 # number of 1s allowed in dna string at the start; "power" of each cell at the start shd be low and get higher as generations go
    # can start with half of 24 (total)
    
    # insert others to change "global" params for all bacteria

    def __init__(self, x, y, isChild = False):

        # current coordinate
        self.x = x
        self.y = y

        # generate a unique id for the bacteria
        while True:
            new_id = random.randint(100000, 999999)
            if new_id not in Bacteria.EXISTING_IDS:
                break
        self.id = new_id
        Bacteria.EXISTING_IDS.add(self.id)

        # generate dna string
        # cap number of 1s at 3/4 of all strings - we want high values for each eventually aft each generation but which specs are more important? how do the values change?
        # what about children dna? self-generate or take from parents? ideally must be input argument
        self.isChild = isChild
        if self.isChild == False:
            self.dna = self.generate_dna(Bacteria.START_POWER)
            # self.dna = self.generate_dna() if self.child = False else self.inherit(parent1,parent2)

        # decode genetic string into traits
        self.traits = {
            'tendrils': int(self.dna[0:4], 2),  # first 4 characters represent trait1; all max value is 15, min is 0 for 4 bit binary number with base 2
            'absorption': int(self.dna[4:8], 2),  # next 4 characters represent trait2
            'membrane': int(self.dna[8:12], 2),  # next 4 characters represent trait3
            'photosynthesis': int(self.dna[12:16], 2),  # next 4 characters represent trait4
            'legs': int(self.dna[16:20], 2),  # next 4 characters represent trait5
            'HP' : int(self.dna[20:24], 2)  # last 5 characters represent trait6
        }

        self.tendrils = self.traits['tendrils']
        self.absorption = self.traits['absorption']
        self.membrane = self.traits["membrane"]
        self.photosynthesis = self.traits['photosynthesis']
        self.legs = self.traits['legs']
        self.hp = self.traits['HP']*100
        colors = (RED, BLACK, GREEN, YELLOW, BLUE, WHITE)
        self.color = random.choice(colors)

        # simple raytrace element - 0,0 top left, y+ downwards, x+ rightwards
        self.tendrils_lines = {
            'top': [(x, y - i) for i in range(1, int(self.tendrils) + 1)],
            'top_right': [(x + i, y - i) for i in range(1, int(self.tendrils) + 1)],
            'right': [(x + i, y) for i in range(1, int(self.tendrils) + 1)],
            'down_right': [(x + i, y + i) for i in range(1, int(self.tendrils) + 1)],
            'down': [(x, y + i) for i in range(1, int(self.tendrils) + 1)],
            'down_left': [(x - i, y + i) for i in range(1, int(self.tendrils) + 1)],
            'left': [(x - i, y) for i in range(1, int(self.tendrils) + 1)],
            'top_left': [(x - i, y - i) for i in range(1, int(self.tendrils) + 1)]
        }
    
    # generates the DNA string - this is only when spawning, children bacteria shoud have another function 'inherit(parent1, parent 2)'
    def generate_dna(self, start_power, length=24): # length should be no of traits x 4
        self.dna = ''.join(random.choice('01') for _ in range(length))
        ones_count = self.dna.count('1')
        while ones_count != start_power:
            if ones_count < start_power:
                # add '1's
                index = random.randint(0, length - 1)
                if self.dna[index] == '0':
                    self.dna = self.dna[:index] + '1' + self.dna[index + 1:]
                    ones_count += 1
            else:
                # remove '1's
                index = random.randint(0, length - 1)
                if self.dna[index] == '1':
                    self.dna = self.dna[:index] + '0' + self.dna[index + 1:]
                    ones_count -= 1
        return self.dna
    
    # draws main body
    def draw(self, screen):
        # draw body
        pygame.draw.rect(screen, self.color, (self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # also draws tendrils lines along with bacteria
        for _, positions in self.tendrils_lines.items():
            for pos in positions:
                pygame.draw.rect(screen, self.color, (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)
        
        # display ID and HP overlayed on top of the main body/coordinate
        font = pygame.font.SysFont(None, 12)
        text_id = font.render(f"ID: {self.id}", True, WHITE)
        text_hp = font.render(f"HP: {self.hp}", True, WHITE)
        text_dna = font.render(f"DNA: {self.dna}", True, WHITE)
        screen.blit(text_id, (self.x * TILE_SIZE, self.y * TILE_SIZE - TILE_SIZE))
        screen.blit(text_hp, (self.x * TILE_SIZE, self.y * TILE_SIZE + TILE_SIZE))
        screen.blit(text_dna, (self.x * TILE_SIZE, self.y * TILE_SIZE + 2*TILE_SIZE))

    def update_tendrils_lines(self):
        self.tendrils_lines = {
            'top': [(self.x, self.y - i) for i in range(1, int(self.tendrils) + 1)],
            'top_right': [(self.x + i, self.y - i) for i in range(1, int(self.tendrils) + 1)],
            'right': [(self.x + i, self.y) for i in range(1, int(self.tendrils) + 1)],
            'down_right': [(self.x + i, self.y + i) for i in range(1, int(self.tendrils) + 1)],
            'down': [(self.x, self.y + i) for i in range(1, int(self.tendrils) + 1)],
            'down_left': [(self.x - i, self.y + i) for i in range(1, int(self.tendrils) + 1)],
            'left': [(self.x - i, self.y) for i in range(1, int(self.tendrils) + 1)],
            'top_left': [(self.x - i, self.y - i) for i in range(1, int(self.tendrils) + 1)]
        }
    
    # handles movement of the bacteria - keep this
    def move(self, direction, step):
        if direction == 'top':
            self.y -= step
        elif direction == 'top_right':
            self.x += step
            self.y -= step
        elif direction == 'right':
            self.x += step
        elif direction == 'down_right':
            self.x += step
            self.y += step
        elif direction == 'down':
            self.y += step
        elif direction == 'down_left':
            self.x -= step
            self.y += step
        elif direction == 'left':
            self.x -= step
        elif direction == 'top_left':
            self.x -= step
            self.y -= step

        # ensures bacteria stays within the grid
        self.x = max(0, min(self.x, GRID_WIDTH - 1))
        self.y = max(0, min(self.y, GRID_HEIGHT - 1))
        
    def roam(self, bacteria_list): # movement pattern ROAM
        # reduce hp as it roams - costs energy to move// remove later
        self.hp -= 1

        # generate random direction and move
        direction = random.choice(['top', 'top_right', 'right', 'down_right', 'down', 'down_left', 'left', 'top_left'])
        step = 1
        self.move(direction, step)

        # check for OBVIOUS collisions
        next_positions = [(bacteria.x, bacteria.y) for bacteria in bacteria_list]
        next_positions.remove((self.x, self.y))  # remove current position for self-collision check
        if (self.x, self.y) in next_positions:
            # collision (overlap) detected
            # print(f"collision at {self.x},{self.y}")
            # randomly move to an empty adjacent cell within 1 block of collision cell
            adjacent_cells = [(x, y) for x in range(self.x - 1, self.x + 2) for y in range(self.y - 1, self.y + 2) if (x, y) not in next_positions]
            if adjacent_cells:
                self.x, self.y = random.choice(adjacent_cells)
    
    # death - all can die
    def die(self, bacteria_list):
    # check if HP is below 0, remove the bacteria
        global deaths # access global var
        if self.hp <= 0:
            bacteria_list.remove(self)
            deaths += 1
            

# ---- ---- ---- ---- end of Bacteria class

# pygame setup
screen = pygame.display.set_mode( (WIDTH,HEIGHT) ) #takes in a tuple as argument; not 2 numbers
clock = pygame.time.Clock()

def draw_grid():
    
    for row in range(GRID_HEIGHT):
        pygame.draw.line(screen,BLACK,start_pos=(0,row*TILE_SIZE),end_pos=(WIDTH,row*TILE_SIZE))
    for col in range(GRID_WIDTH):
        pygame.draw.line(screen,BLACK,start_pos=(col*TILE_SIZE,0),end_pos=(col*TILE_SIZE,HEIGHT))

# global variable setup for game to work
bacteria_list = []
deaths = 0

# main pygame program
def main():
    global bacteria_list
    INIT_NUM_BACTERIA = 5
    running = True

    # create initial bacteria
    for _ in range(INIT_NUM_BACTERIA):
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        bacteria_list.append(Bacteria(x, y))
    
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            # pygame.QUIT is a value, pygame.quit() is a function call (the X button)
            # this enables the CLOSE button to work
            if event.type == pygame.QUIT:
                running = False
                
        screen.fill(GREY)
        # highlight_rect = pygame.Rect(3*TILE_SIZE, 3*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        # pygame.draw.rect(screen, (255, 0, 0), highlight_rect, 0)
        # here we use draw_grid to draw the positions on top of the grid
        draw_grid()

        # draw and move bacteria 
        for bacteria in bacteria_list:
            bacteria.draw(screen)
            bacteria.roam(bacteria_list) # --- to encapsulate into 1 function eg .live()
            bacteria.update_tendrils_lines()
            bacteria.die(bacteria_list)
        
        # statistics; quite hard coded
        font = pygame.font.SysFont(None, 24)  # define font
        # population count
        bacteria_count_text = font.render(f"Bacteria count: {len(bacteria_list)}", True, WHITE)  # render text
        screen.blit(bacteria_count_text, (10, 10))  # hard coded coordinates for placement of text
        # death count
        deaths_count = font.render(f"Death count: {deaths}", True, WHITE)
        screen.blit(deaths_count, (200,10))
        # end of sim status
        if len(bacteria_list) == 0:
            ending = font.render("All bacteria have died. Simulation ended.", True, WHITE)
            screen.blit(ending, (250, 350))

        # updates time step
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()