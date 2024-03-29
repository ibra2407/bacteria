# TODO
'''
Priorities: (1), (2), (3)
Main Logic:
1. run behaviour (1) - 20-80% hp will run if detect BL if self is not BL
2. photosynthesis - sunlight zones (1)
3. play with parameters (ranges, values based on traits) (3)
4. absorb function fix -> enable any bacteria to eat each other; only if BL then rules change

Analysis:
1. add init number as line on graph (1)
2. return output properly in a list, try show steady state parameters (need to find this too), link to pt2 of SMA - burn in period, true expected steady state given a set of parameters (2)
3. general observations

Aesthetics:
1. UI design of bacteria & background (graphics) (2)
2. menu screen (to set parameters or smth) (2)

Performance:
1. make the matplotlib a bit smoother and can actually use to see shit (3)
2. limit number of bacteria

Completed:
1. investigate "blooming" of population, find out why child always dies so fast (2) - mating function issue
2. Mating fucntion fixed but still able to produce inferior offsrping with less power than parents somehow (not intended)
'''

# install these libraries
import pygame
import random
import math
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
import numpy as np
import tkinter as tk
from tkinter import scrolledtext

# initialise a pygame instance
pygame.init()

# global variable to set number of bact in simulation
sim_num_bact = 10

# pygame screen elements
WIDTH, HEIGHT = 400,400 # default 800,800
TILE_SIZE = 10

# # if need to bound the simulation area use this
# LEFT_SIM_BOUND_WIDTH = WIDTH // 4  # width of the left SIM_BOUND (in pixels)
# RIGHT_SIM_BOUND_WIDTH = WIDTH - LEFT_SIM_BOUND_WIDTH  # width of the right SIM_BOUND (in pixels)

# GRID_WIDTH = RIGHT_SIM_BOUND_WIDTH // TILE_SIZE  # width of the grid (in no. of tiles)
# GRID_HEIGHT = HEIGHT // TILE_SIZE  # weight of the grid (in no. of tiles)

GRID_WIDTH = WIDTH // TILE_SIZE
GRID_HEIGHT = HEIGHT // TILE_SIZE
FPS = 120 # clock ticks {FPS} times a real second

# simple RGB colours
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)

PINK = (255, 192, 203)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
PURPLE = (255, 0, 255)

# ---- ---- ---- ---- bacteria class ---- ---- ---- ----
class Bacteria:

    # BACTERIA SIMULATION PARAMS; access in class functions as Bacteria.
    EXISTING_IDS = set()  # store generated IDs, ensuring they dont repeat
    START_POWER = 8 # number of 1s allowed in dna string at the start; "power" of each cell at the start shd be low and get higher as generations go
    # can start with half of 24 (total)
    MAX_POWER = 18 # can only choose to max out 4 out of 6 traits; 10% chance of a child to increase its power
    MATING_COOLDOWN = 3000
    # insert others to change "global" params for all bacteria

    def __init__(self, x, y, isChild = False, dna = None):

        # current coordinate
        self.x = x
        self.y = y

        # lifespan to measure life
        self.lifespan = 0

        self.last_mate_time = 0

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
        else:
            self.dna = dna

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
        self.absorb_range = max(1, math.floor(self.absorption/2))

        self.membrane = self.traits["membrane"]

        self.photosynthesis = self.traits['photosynthesis']

        self.legs = self.traits['legs']

        self.hp = 0.8*max(200, self.traits['maxHP']*200) # start with 80% hp so dont spawn in mating mood
        self.maxHP = max(200, self.traits['maxHP']*200) # need a separate variable; self.hp deducts stuff

        # Bacteria STATES here
        # set both to False initially
        self.BloodlustOn = False
        self.MatingOn = False

        # colours - to eventually be replaced with animated object
        colour_dict = {
            "RED": RED,
            "ORANGE": ORANGE,
            "YELLOW": YELLOW,
            "GREEN": GREEN,
            "BLUE": BLUE,
            "CYAN": CYAN,
            "PURPLE": PURPLE,
            "PINK": PINK
        }
        # select a random colour key from colour_dict
        colour_name = random.choice(list(colour_dict.keys()))

        # set the colour attribute using the selected colour key
        self.colour = colour_dict[colour_name]

        # set the colour name attribute
        self.colour_name = colour_name

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
        # print(prob_movement, prob_hunt, prob_mate) # prints probabilities at each time step

        self.hp -= 1 # on top of movement hp deduction

        # when just spawn, sit still for a while

        # # HP > 80%; definitely wants to mate
        # self.MatingOn = True
        # # finds a mate
        if(self.hp > 0.8*self.maxHP):
            self.MatingOn = True
            self.BloodlustOn = False

        # # HP 20-80%
        if (self.hp > 0.2*self.maxHP and self.hp <= 0.8*self.maxHP):
            if prob_hunt > 0.8:
                self.BloodlustOn = True
                self.MatingOn = False
            if prob_mate > 0.8:
                self.BloodlustOn = False
                self.MatingOn = True
            if prob_movement > 0.6: # might require balancing
                self.BloodlustOn = False
                self.MatingOn = False

        # # HP < 20%; definitely wants to hunt
        # self.BloodlustOn = True
        if self.hp <= 0.2*self.maxHP:
            self.BloodlustOn = True
            self.MatingOn = False

        # Bacteria states
        # check if there are other bacteria in tendrils lines - can try implement see() for cleaner code, but dont rly matter
        for direction, positions in self.tendrils_lines.items():
            for pos in positions:
                for bacteria in bacteria_list:
                    if bacteria != self and (bacteria.x, bacteria.y) == pos:
                        # first other bacteria in tendrils lines found

                        # excited case
                        if self.BloodlustOn or self.MatingOn:
                            # print(f"Bacteria {self.colour_name} is on the chase for bacteria {bacteria.colour_name}")
                            self.chase(direction)

                            # hunting case
                            if self.BloodlustOn:
                                self.absorb(bacteria_list)
                            
                            # mating case
                            if self.MatingOn:
                                if prob_mate > 0.5:
                                    self.mate(bacteria_list)
                            
                            
        if self.BloodlustOn or self.MatingOn:
            self.frantic()
        # default state
        if not self.BloodlustOn and not self.MatingOn and prob_movement > 0.4: # 40% chance to sit and chill if not excited
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
        # self.x = max(LEFT_SIM_BOUND_WIDTH // TILE_SIZE, min(self.x, (WIDTH - 1) // TILE_SIZE))
        # self.y = max(0, min(self.y, (HEIGHT - 1) // TILE_SIZE))

    def chase(self, direction):
        step = max(1, math.floor(self.legs/2))
        self.hp -= math.floor(self.legs/2)
        self.move(direction, step)
                        
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
        step = 3
        self.move(direction, step)
    
    # death - all can die
    def die(self, bacteria_list):
    # check if HP is below 0, remove the bacteria
        global deaths # access global var
        if self.hp <= 0:
            bacteria_list.remove(self)
            deaths += 1
            # add dead bacteria to dictionary
            bacteria_lifespan[self.id] = {
            'lifespan': self.lifespan,
            'dna': self.dna,
            'traits': self.traits,
            'isChild': self.isChild
        }
    
    # absorption logic
    def absorb(self, bacteria_list):
        # set the range
        absorb_range = self.absorb_range
        # check if any other bacteria is within the bite range
        for bacteria in bacteria_list:
            if bacteria != self and abs(self.x - bacteria.x) <= absorb_range and abs(self.y - bacteria.y) <= absorb_range: # only within range
                # only higher absorption wins out;
                if self.absorption > bacteria.absorption:
                    # case 1: enable absoprtion if can penetrate armor
                    if self.absorption > bacteria.membrane:
                        absorb_damage = min(self.absorption - bacteria.membrane, bacteria.hp)  # set to depend on absorption value (20 is just example); also prevents absorption from regaining more than other bacterias hp
                        self.hp += round(absorb_damage,2)
                        bacteria.hp -= absorb_damage
                    # if the other guy defense is too high, deal only 1 damage. cannot absorb more than remaining bacteria hp (if remaining bacteria hp is 1)
                    else:
                        absorb_damage = min(1, bacteria.hp) 
                        self.hp += round(absorb_damage,2)
                        bacteria.hp -= absorb_damage

                    print(f"Bacteria {self.colour_name} bit Bacteria {bacteria.colour_name} at position {bacteria.x},{bacteria.y}.")
                    print(f"After absorbing: {self.colour_name} HP: {self.hp}, {bacteria.colour_name} HP: {bacteria.hp}")

                    # check if the other bacteria's HP is zero after absorption
                    if bacteria.hp <= 0:
                        print(f"Bacteria {bacteria.colour_name} has been fully eaten by Bacteria {self.colour_name}!")
                    return
    
    # mating logic using DNA
    def mate(self, bacteria_list):
        # set the range
        pheromone_range = 3
        for bacteria in bacteria_list:
            # check if any other bacteria is within mating range
            if bacteria != self and abs(self.x - bacteria.x) <= pheromone_range and abs(self.y - bacteria.y) <= pheromone_range: # only within range
                # both must be in mating mood
                if self.MatingOn and bacteria.MatingOn:
                    # check cooldown before mating
                    current_time = pygame.time.get_ticks()
                    if current_time - self.last_mate_time >= Bacteria.MATING_COOLDOWN:
                        child_dna = self.inherit(self.dna, bacteria.dna)
                        if child_dna == "":
                            return
                        else:
                            # create child with inherited traits and DNA
                            child = Bacteria(self.x, self.y, isChild=True, dna = child_dna)
                            # child should spawn where the parents mated
                            child.x = (self.x + bacteria.x) // 2
                            child.y = (self.y + bacteria.y) // 2
                            # child shd start with half hp
                            child.hp = 0.5*child.maxHP

                            # append child to bacteria list
                            bacteria_list.append(child)

                            # parents sacrifice 10% hp to create child
                            self.hp = 0.9*self.hp
                            bacteria.hp = 0.9*bacteria.hp

                            self.last_mate_time = current_time

                            print(f"Bacteria {self.colour_name} mated with {bacteria.colour_name} and gave birth to {child.colour_name}")

        self.MatingOn = False
        bacteria.MatingOn = False


    # inheritance logic - to get dna from mate() and pass it to inherit(), which will set the child bacteria new dna
    # use factory method
    @staticmethod
    def inherit(dna1, dna2):
        # Step 1:
        # Turn both DNA strings into lists of how many traits there are with each entry being a value
        dna_trait1 = [int(dna1[i:i+4], 2) for i in range(0, len(dna1), 4)]
        dna_trait2 = [int(dna2[i:i+4], 2) for i in range(0, len(dna2), 4)]

        # Step 2:
        # Get the max value
        max_value1 = max(dna_trait1)
        max_value2 = max(dna_trait2)

        # Check if the difference in the number of ones between parents is 0 or 1
        num_ones1 = dna1.count('1')
        num_ones2 = dna2.count('1')
        ones_difference = abs(num_ones1 - num_ones2)
        if ones_difference > 1:
            return "" # "Parents cannot mate."

        # Step 3:
        # Directly copy the DNA strings corresponding to the traits of both parents to the child DNA
        child_dna = ''
        inherited_indices = set()  # Store indices of inherited trait segments
        for i in range(len(dna_trait1)):
            if dna_trait1[i] == max_value1:
                child_dna += dna1[i*4:i*4+4]
                inherited_indices.add(i)
            elif dna_trait2[i] == max_value2:
                child_dna += dna2[i*4:i*4+4]
                inherited_indices.add(i)
            else:
                child_dna += '0000'  # placeholder for non-max traits

        # Step 4:
        # Ensure the number of 1s is at least the max of the parents' number of 1s
        max_ones = max(num_ones1, num_ones2)

        # If child has fewer ones than max of parents, add extra ones
        child_ones = child_dna.count('1')
        remaining_ones = max_ones - child_ones
        
        # Iterate through the non-inherited portions to add ones
        for i in range(len(dna_trait1)):
            if i not in inherited_indices:
                # If the remaining ones are already added, break the loop
                if remaining_ones == 0:
                    break
                # Add one to the non-inherited portion
                child_dna = child_dna[:i*4] + '1' + child_dna[i*4+1:]
                child_ones += 1
                remaining_ones -= 1

        # Step 5:
        # With 50% chance, add an extra 1
        if random.random() < 0.5:
            index = random.randint(0, len(child_dna) - 1)
            if index // 4 not in inherited_indices:  # Check if the index is not in an inherited trait segment
                child_dna = child_dna[:index] + '1' + child_dna[index+1:]
                child_ones += 1

        # Step 6:
        # Ensure that the number of 1s in the child does not exceed MAX_POWER
        if child_ones > Bacteria.MAX_POWER:
            return "" # "Child is too powerful"

        return child_dna
    
    # running logic against hungry bacteria
    def run(self, bacteria_list):
        pass

    # sunlight zone behaviour
    def photosynthesise(self, zone_value):
        pass

    # ---- FOR PYGAME SCREEN ----

    # draws main body
    def draw(self, screen):
        # draw body
        pygame.draw.rect(screen, self.colour, (self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # also draws tendrils lines along with bacteria
        for _, positions in self.tendrils_lines.items():
            for pos in positions:
                pygame.draw.rect(screen, self.colour, (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)
        
        # draw absorb range as a circle
        absorb_range = self.absorb_range
        pygame.draw.circle(screen, self.colour, (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2), absorb_range * TILE_SIZE, 1)
        
        # display ID and HP overlayed on top of the main body/coordinate
        font = pygame.font.SysFont(None, 12)
        text_id = font.render(f"ID: {self.id}", True, WHITE)
        text_hp = font.render(f"HP: {self.hp}", True, WHITE)
        text_dna = font.render(f"DNA: {self.dna}", True, WHITE)
        screen.blit(text_id, (self.x * TILE_SIZE, self.y * TILE_SIZE - TILE_SIZE))
        screen.blit(text_hp, (self.x * TILE_SIZE, self.y * TILE_SIZE + TILE_SIZE))
        screen.blit(text_dna, (self.x * TILE_SIZE, self.y * TILE_SIZE + 2*TILE_SIZE))

        # bloodlust and mating flags
        font2 = pygame.font.SysFont(None, 18)
        if self.BloodlustOn:
            text_bloodlust = font2.render("Bloodlust", True, RED)
            screen.blit(text_bloodlust, (self.x * TILE_SIZE, self.y * TILE_SIZE + 3*TILE_SIZE))
        elif self.MatingOn:
            text_mating = font2.render("Mating", True, BLUE)
            screen.blit(text_mating, (self.x * TILE_SIZE, self.y * TILE_SIZE + 3*TILE_SIZE))

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

# draw bounding box for bacteria simulation
# def draw_outline():
#     pygame.draw.rect(screen, BLACK, (LEFT_SIM_BOUND_WIDTH, 0, RIGHT_SIM_BOUND_WIDTH, HEIGHT), 2)

# list to store bacteria objects and their lifespan
bacteria_lifespan = {}

# function to update bacteria lifespan at each time step
def update_bacteria_lifespan(bacteria_list):
    for bacteria in bacteria_list:
        bacteria.lifespan += 1

# global variable setup for game to work
bacteria_list = []
deaths = 0

# analytics section
MAX_DATA_POINTS = 10000  # maximum number of data points to display on the graph

def update_graph(bacteria_count_history, deaths_history):
    plt.clf()  # Clear the previous plot

    # plot bacteria count over time
    plt.subplot(2, 1, 1)
    plt.plot(bacteria_count_history, color='blue')
    plt.title('Bacteria Count Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Bacteria Count')

    # ddd the current bacteria count as a dot at the most recent point
    current_bacteria_count = len(bacteria_list)
    plt.scatter(len(bacteria_count_history) - 1, current_bacteria_count, color='red', label=f'Current Bacteria Count: {current_bacteria_count}')
    plt.legend()

    # Add initial bacteria count as a horizontal dotted line
    plt.axhline(y=sim_num_bact, color='gray', linestyle='--', label=f'Starting Count: {sim_num_bact}')
    plt.legend()

    # plot death count over time
    plt.subplot(2, 1, 2)
    plt.plot(deaths_history, color='red')
    plt.title('Deaths Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Deaths')

    # add the current death count as a dot at the most recent point
    current_deaths = deaths
    plt.scatter(len(deaths_history) - 1, current_deaths, color='blue', label=f'Current Death Count: {current_deaths}')
    plt.legend()

    plt.tight_layout()  # Adjust layout to prevent overlap
    plt.draw()
    plt.pause(0.001)

# main pygame program
def main():
    global bacteria_list
    INIT_NUM_BACTERIA = sim_num_bact

    # initialize data lists to store history
    bacteria_count_history = []
    deaths_history = []

    # flag to stop graph
    update_graph_flag = True
    
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
        # draw_grid()
        # draw_outline()

        # draw and move bacteria 
        for bacteria in bacteria_list:
            bacteria.draw(screen)
            bacteria.live(bacteria_list) # --- to encapsulate all actions into 1 function eg .live()
            bacteria.update_tendrils_lines()
            bacteria.die(bacteria_list)
        
        # updates bacteria lifespan in the list
        update_bacteria_lifespan(bacteria_list)
        
        # statistics; quite hard coded
        font2 = pygame.font.SysFont(None, 24)  # define font
        # population count
        bacteria_count_text = font2.render(f"Bacteria count: {len(bacteria_list)}", True, WHITE)  # render text
        screen.blit(bacteria_count_text, (10, 10))  # hard coded coordinates for placement of text

        # death count
        deaths_count = font2.render(f"Death count: {deaths}", True, WHITE)
        screen.blit(deaths_count, (160,10))

        # update history lists
        bacteria_count_history.append(len(bacteria_list))
        deaths_history.append(deaths)

        # limit history lists to a maximum number of data points
        if len(bacteria_count_history) > MAX_DATA_POINTS:
            bacteria_count_history = bacteria_count_history[-MAX_DATA_POINTS:]
        if len(deaths_history) > MAX_DATA_POINTS:
            deaths_history = deaths_history[-MAX_DATA_POINTS:]

        # update the graph if flag is True and bacteria list is not empty
        if update_graph_flag and len(bacteria_list) > 0:
            update_graph(bacteria_count_history, deaths_history)

        # stop updating graph if bacteria list is empty
        if len(bacteria_list) == 0:
            update_graph_flag = False

        # # end of sim status
        if len(bacteria_list) == 0:
            # sim = font2.render("Simulation ended.", True, WHITE)
            # screen.blit(sim, (WIDTH//2, HEIGHT//2))
            # sort bacteria by lifespan
            sorted_bacteria = sorted(bacteria_lifespan.items(), key=lambda x: x[1]['lifespan'], reverse=True)
            
            # define font for displaying text on screen
            font3 = pygame.font.SysFont(None, 24)

            # display rankings
            y_offset = 60
            gap = 30

            # display champion
            champion_id, champion_details = sorted_bacteria[0]
            text_dna = font3.render(f"DNA of the champion bacteria: {champion_details['dna']}", True, WHITE)
            screen.blit(text_dna, (10, y_offset))
            print(f"Longest living Bacteria has DNA {champion_details['dna']}")

            traits_text = font3.render("Trait values:", True, WHITE)
            screen.blit(traits_text, (10, y_offset + gap))
            for i, (trait, value) in enumerate(champion_details['traits'].items()):
                text_trait = font3.render(f"{trait}: {value}", True, WHITE)
                screen.blit(text_trait, (10, y_offset + (i+2)*gap))
                print(f"Champion bacteria traits: {trait}: {value}")
            
            # print if the champion bacteria is a child or not
            child_text = "Child" if champion_details['isChild']==True else "not a child"
            text_child = font3.render(f"Champion is a {child_text}", True, WHITE)
            screen.blit(text_child, (10, y_offset + (i + 3) * gap))
            print(f"Champion is {child_text}")

            # display top 10 bacteria with longest lifespans
            ranking_text = font3.render("Top 10 Ranking of Bacteria according to Lifespan:", True, WHITE)
            screen.blit(ranking_text, (20, y_offset + (i + 4) * gap))

            for j, (bacteria_id, details) in enumerate(sorted_bacteria[:10], start=1):
                text_rank = f"{j}. Lifespan: {details['lifespan']}, {'Child' if details['isChild'] else 'NotChild'}"
                for trait, value in details['traits'].items():
                    text_rank += f", {trait}: {value}"
                
                # render and display the text
                text_rank_rendered = font3.render(text_rank, True, WHITE)
                screen.blit(text_rank_rendered, (20, y_offset + (j+9) * gap))
            
            print(f"Top 10 rankings:")
            for j, (bacteria_id, details) in enumerate(sorted_bacteria[:10], start=1):
                print(f"{j}. Lifespan: {details['lifespan']}, {'Child' if details['isChild'] else 'NotChild'}, DNA: {details['dna']}")
                for trait, value in details['traits'].items():
                    print(f"   {trait}: {value}")
            
            break

                        
            
        # updates time step
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()