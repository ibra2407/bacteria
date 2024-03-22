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

        # find lifetime
        # self.lifetime = see who lives the longest

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
            'membrane': int(self.dna[8:12], 2),  #
            'photosynthesis': int(self.dna[12:16], 2),
            'legs': int(self.dna[16:20], 2),
            'maxHP' : int(self.dna[20:24], 2)
        }

        # Bacteria TRAIT attributes here
        self.tendrils = max(1, self.traits['tendrils']) # range: 1 to 15; minimally each one shd have a bit of tendril

        self.absorption = self.traits['absorption']

        self.membrane = self.traits["membrane"]

        self.photosynthesis = self.traits['photosynthesis']

        self.legs = self.traits['legs']

        self.hp = self.traits['maxHP']*30

        self.maxHP = self.traits['maxHP']*30 # need a separate variable; self.hp deducts stuff

        # Bacteria STATES here

        self.isBloodlustOn = False
        # HP<30%
        # to activate chase and bite
        # indiscriminate bacteria will be bitten

        self.isMatingOn = False
        # HP>70%
        # to activate mating, chase other isMatingOn bacteria
        # once childProduced = TRUE, turn on



        # colors - to eventually be replaced with animated object
        colors = (RED, GREEN, YELLOW, BLUE, CYAN, PURPLE)
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

    # --- MAIN FUNCTION FOR BACTERIA LIFE & ACTIONS ---
    def live(self, bacteria_list):

        # random number generator to determine actions
        prob_movement = random.uniform(0,1)
        prob_mate = random.uniform(0,1)
        prob_hunt = random.uniform(0,1)

        # when just spawn, sit still for a while

        # # HP > 70%; definitely wants to mate
        # self.isMatingOn = True
        # # finds a mate

        # # HP 30-70%; if it doesnt hunt, it will mate?
        # if prob_hunt > 0.75:
        #     self.isBloodlustOn = True
        # if prob_mate > 0.75:
        #     self.isMatingOn = True

        # # HP < 30%; definitely wants to kill
        # self.isBloodlustOn = True
        if self.hp <= 0.3*self.maxHP:
            self.isBloodlustOn = True

        # movement states
        if self.isBloodlustOn == True or self.isMatingOn:
            self.frantic()
        
        if self.isBloodlustOn == False and self.isMatingOn == False:
            self.roam()

        # check for OBVIOUS collisions & prevent
        next_positions = [(bacteria.x, bacteria.y) for bacteria in bacteria_list]
        next_positions.remove((self.x, self.y))  # remove current position for self-collision check
        if (self.x, self.y) in next_positions:
            # collision (overlap) detected
            # print(f"collision at {self.x},{self.y}")
            # randomly move to an empty adjacent cell within 1 block of collision cell
            adjacent_cells = [(x, y) for x in range(self.x - 1, self.x + 2) for y in range(self.y - 1, self.y + 2) if (x, y) not in next_positions]
            if adjacent_cells:
                self.x, self.y = random.choice(adjacent_cells)
        
    # --- END OF MAIN FUNCTION FOR BACTERIA LIFE & ACTIONS ---
    
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
        
    def roam(self): # movement pattern ROAM
        # reduce hp as it roams - costs energy to move// remove later
        self.hp -= 1

        # generate random direction and move
        direction = random.choice(['top', 'top_right', 'right', 'down_right', 'down', 'down_left', 'left', 'top_left'])
        step = 1
        self.move(direction, step)
    
    def frantic(self): # movement pattern ROAM
        # reduce hp as it roams - costs energy to move// remove later
        self.hp -= 1

        # generate random direction and move
        direction = random.choice(['top', 'top_right', 'right', 'down_right', 'down', 'down_left', 'left', 'top_left'])
        step = 10
        self.move(direction, step)
    
    # death - all can die
    def die(self, bacteria_list):
    # check if HP is below 0, remove the bacteria
        global deaths # access global var
        if self.hp <= 0:
            bacteria_list.remove(self)
            deaths += 1
    
    # ---- FOR PYGAME SCREEN ----
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

    # function to make sure tendrils show each time step
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
    # ---- END OF PYGAME SCREEN FUNCTIONS ----
            

# ---- ---- ---- ---- end of Bacteria class

# pygame setup
screen = pygame.display.set_mode( (WIDTH,HEIGHT) ) #takes in a tuple as argument; not 2 numbers
clock = pygame.time.Clock()

def draw_grid():
    
    for row in range(GRID_HEIGHT):
        pygame.draw.line(screen,BLACK,start_pos=(0,row*TILE_SIZE),end_pos=(WIDTH,row*TILE_SIZE))
    for col in range(GRID_WIDTH):
        pygame.draw.line(screen,BLACK,start_pos=(col*TILE_SIZE,0),end_pos=(col*TILE_SIZE,HEIGHT))

# dictionary to store bacteria objects and their lifespan
bacteria_lifespan = {}

# function to update bacteria lifespan at each time step
def update_bacteria_lifespan(bacteria_list):
    for bacteria in bacteria_list:
        if bacteria.id not in bacteria_lifespan:
            bacteria_lifespan[bacteria.id] = 0
        bacteria_lifespan[bacteria.id] += 1

# function to print the ranking and details of the longest-living bacteria
def print_longest_living_bacteria():
    sorted_bacteria_lifespan = sorted(bacteria_lifespan.items(), key=lambda x: x[1], reverse=True)
    print("Ranking of Bacteria:")
    for i, (bacteria_id, lifespan) in enumerate(sorted_bacteria_lifespan):
        print(f"Rank {i+1}: Bacteria ID {bacteria_id}, Lifespan: {lifespan} time steps")
    longest_living_bacteria_id, longest_lifespan = sorted_bacteria_lifespan[0]
    print(f"\nThe longest-living bacteria: Bacteria ID {longest_living_bacteria_id}, Lifespan: {longest_lifespan} time steps")


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
            bacteria.live(bacteria_list) # --- to encapsulate all actions into 1 function eg .live()
            bacteria.update_tendrils_lines()
            bacteria.die(bacteria_list)
        
        # updates bacteria lifespan in the list
        update_bacteria_lifespan(bacteria_list)
        
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
            # print rankings too when len(bacteria_list) == 0
            y_offset = 100
            sorted_bacteria_lifespan = sorted(bacteria_lifespan.items(), key=lambda x: x[1], reverse=True)
            text_lines = ["Ranking of Bacteria:"]
            for i, (bacteria_id, lifespan) in enumerate(sorted_bacteria_lifespan):
                text_lines.append(f"Rank {i+1}: Bacteria ID {bacteria_id} {bacteria.color}, Lifespan: {lifespan} time steps")
            longest_living_bacteria_id, longest_lifespan = sorted_bacteria_lifespan[0]
            text_lines.append(f"\nThe longest-living bacteria: Bacteria ID {longest_living_bacteria_id}, Lifespan: {longest_lifespan} time steps")
            for i, line in enumerate(text_lines):
                text = font.render(line, True, WHITE)
                screen.blit(text, (10, y_offset + i * 20))

        # updates time step
        pygame.display.update()

    pygame.quit()
    # print the ranking and details of the longest-living bacteria - only print when pygame is closed
    print_longest_living_bacteria()

if __name__ == "__main__":
    main()