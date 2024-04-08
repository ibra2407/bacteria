# install these libraries
import pygame
import io
import os
import random
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pandas as pd
from datetime import datetime
import openpyxl

# ---- ---- ---- pygame application setup ---- ---- ----

# initialise a pygame instance
pygame.init()

# screen resolution
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

# set pygame window size & where it pops up on screen
window_width = 1500
window_height = 750
# window_size = (window_width, window_height)

# # create pygame window
# screen = pygame.display.set_mode(window_size)

# calculate position for the top-left corner of the pygame window
top_left_x = (screen_width - window_width) // 2
top_left_y = (screen_height - window_height) // 2

# set Pygame window position
os.environ['SDL_VIDEO_WINDOW_POS'] = f'{top_left_x},{top_left_y}'

# ---- ---- ---- end of pygame application setup ---- ---- ----

####

# ---- ---- ---- global variables & parameters ---- ---- ----

# global variable to set number of bact in simulation (initial number of bacteria)
sim_num_bact = 20
# set mating hp threshold (at this % of HP, bacteria will be in Mating mood)
matingHP = 0.7
# set hungry hp threshold (at this % of HP, bacteria will be in Hungry mood)
bloodHP = 0.3

# number of 1s allowed in dna string at the start; "power" of each cell at the start shd be low and get higher as generations go
BCTR_START_POWER = 8 

# can only choose to max out 4 out of 6 traits; 10% chance of a child to increase its power; only 18 out of 24 DNA characters can be 1 (other 6 has to be 0)
BCTR_MAX_POWER = 18 

# cooldown time in miliseconds for bacteria mating
BCTR_MATING_COOLDOWN = 5000

# max history limit for matplotlib graph
MAX_DATA_POINTS = 20000

# multipliers for trait impacts
M_absorption = 2 # multiplicative scaling for absorption; the higher, the greater the effect of the absorption trait
M_membrane = 0.8 # logarithmic scaling; quite sensitive; the lower, the greater the effect of the membrane trait
# absorb_damage = min(self.absorption*M_absorption*((bacteria.membrane/16)**M_membrane), bacteria.hp)

M_photosynthesis = 2 # efficacy of photosynthesis; higher, more HP recovered
# hp_gain = sunlight_values[self.y][self.x] * (self.photosynthesis+1) * M_photosynthesis

M_sacrifice = 0.1 # % of maxHP sacrificed to produce child

# cost of living (hp deduction each time step)
C_living = 1

# propensity to hunt & mate when not hungry or mating
prop_hunt = 0.9
prop_mate = 0.9

# propensity to relax back to normalcy
prop_content = 0.9

# probability of successful mating between 2 Mating bacterias
prob_suc_mate = 0.8

# propensity to roam (as opposed to sitting still and staying idle)
prob_roam = 0.5

# empty df/ excel file for data
excel_filename = ""
data = {}
df = pd.DataFrame(data)

# ---- ---- ---- end of global variables & parameters ---- ---- ----

####

# ---- ---- ---- ---- pygame screen elements ---- ---- ---- ----

WIDTH, HEIGHT = 1500,1000 # width need to be div by 3 for nice MPL graph
TILE_SIZE = 10 # size in pixels of each square cell

# if need to bound the simulation area use this
SIM_BOUND_WIDTH =  2 * (WIDTH // 3) # length of screen from 0 to rightmost boundary

GRID_WIDTH = WIDTH // TILE_SIZE  # width of the grid (in no. of tiles)
GRID_HEIGHT = HEIGHT // TILE_SIZE  # weight of the grid (in no. of tiles)

# GRID_WIDTH = WIDTH // TILE_SIZE
# GRID_HEIGHT = HEIGHT // TILE_SIZE
FPS = 300 # clock ticks {FPS} times a real second

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

# ---- ---- ---- ---- end of pygame screen elements ---- ---- ---- ----

####

# ---- ---- ---- ENVIRONMENT code ---- ---- ----

# ---- SUNLIGHT ----
# sunlight definitions
# define sunlight parameters
SUN_RADIUS = SIM_BOUND_WIDTH // 2
SUN_CENTER = (SIM_BOUND_WIDTH // 2, HEIGHT // 2)

# define sunlight values for each cell in the grid based on distance from the center
sunlight_values = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]

for y in range(GRID_HEIGHT):
    for x in range(GRID_WIDTH):
        distance = math.sqrt((x * TILE_SIZE - SUN_CENTER[0]) ** 2 + (y * TILE_SIZE - SUN_CENTER[1]) ** 2)
        if distance <= SUN_RADIUS:
            sunlight_values[y][x] = 1 - (distance / SUN_RADIUS)
        else:
            sunlight_values[y][x] = 0
# print(sunlight_values)

def draw_sun():
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            sunlight = sunlight_values[y][x]
            color = (int(255 * sunlight), int(255 * sunlight), 0)  # pale yellow color based on sunlight value
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, color, rect)

# ---- ---- ---- end of ENVIRONMENT code ---- ---- ----

####

# ---- ---- ---- ---- BACTERIA class ---- ---- ---- ----
class Bacteria:

    # BACTERIA SIMULATION PARAMS; access in class functions as Bacteria.
    EXISTING_IDS = set()  # store generated IDs, ensuring they dont repeat

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
            self.dna = self.generate_dna(BCTR_START_POWER)
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

        # tendril traits
        self.tendrils = max(1, self.traits['tendrils']) # range: 1 to 15; minimally each one shd have a bit of tendril

        # absorption traits & secondary traits
        self.absorption = self.traits['absorption']
        self.absorb_range = max(1, math.floor(self.absorption/2))

        # membrane trait
        self.membrane = self.traits["membrane"]

        # photosynthesis trait
        self.photosynthesis = self.traits['photosynthesis']

        # legs trait
        self.legs = self.traits['legs']

        # maxHP trait
        self.maxHP = max(200, self.traits['maxHP']*200) # need a separate variable; self.hp deducts stuff

        # starting HP attribute
        self.hp = 0.5*max(200, self.traits['maxHP']*200) # start with mating hp so dont spawn in mating mood ( will decrease immediately when they live)
        
        # Bacteria STATES here
        # set both to False initially
        self.HungryOn = False
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
        
        # lifespan increases every passing time step
        self.lifespan += 1
        
        # prevent more than self.maxHP
        if self.hp > self.maxHP:
            self.hp = self.maxHP

        # random number generator to determine actions
        prob_movement = random.uniform(0,1)
        prob_mate = random.uniform(0,1)
        prob_hunt = random.uniform(0,1)
        prob_photosynthesis = random.uniform(0,1)
        # print(prob_movement, prob_hunt, prob_mate) # prints probabilities at each time step

        self.hp -= C_living # on top of movement hp deduction

        # when just spawn, sit still for a while

        # # HP > matingHP; definitely wants to mate
        # self.MatingOn = True
        # # finds a mate
        if(self.hp > matingHP*self.maxHP):
            self.MatingOn = True
            self.HungryOn = False

        # # HP middle zone; random chance
        if (self.hp > bloodHP*self.maxHP and self.hp <= matingHP*self.maxHP):
            if prob_hunt > prop_hunt:
                self.HungryOn = True
                self.MatingOn = False
            if prob_mate > prop_mate:
                self.HungryOn = False
                self.MatingOn = True
            if prob_movement > (1-prop_content): # might require balancing
                self.HungryOn = False
                self.MatingOn = False

        # definitely wants to hunt
        # self.HungryOn = True
        if self.hp <= bloodHP*self.maxHP:
            self.HungryOn = True
            self.MatingOn = False

        # Bacteria states
        # check if there are other bacteria in tendrils lines - can try implement see() for cleaner code, but dont rly matter
        for direction, positions in self.tendrils_lines.items():
            for pos in positions:
                for bacteria in bacteria_list:
                    if bacteria != self and (bacteria.x, bacteria.y) == pos:
                        # first other bacteria in tendrils lines found
                        # excited case
                        if self.HungryOn or self.MatingOn:
                            # print(f"Bacteria {self.colour_name} is on the chase for bacteria {bacteria.colour_name}")
                            self.chase(direction)

                            # hunting case
                            if self.HungryOn:
                                self.absorb(bacteria_list)
                            
                            # mating case
                            if self.MatingOn:
                                if prob_mate > prob_suc_mate: # 80% chance will mate if both horny; actually chance of horny + meet when horny is alr q low so this doesnt matter much
                                    self.mate(bacteria_list)

                        else:
                            # if not Hungry or mating, will just avoid other bacteria thats hungry
                            self.run(direction)
                            
        if self.HungryOn or self.MatingOn:
            self.frantic()
            if sunlight_values[self.y][self.x] > 0 and prob_photosynthesis < self.photosynthesis/15:
                self.HungryOn = False
                self.MatingOn = False
        
        # default state
        if not self.HungryOn and not self.MatingOn:
            if prob_movement > prob_roam:
                self.roam()
        
        # all are able to photosynthesise
        self.photosynthesise(sunlight_values)

        # check for OBVIOUS collisions & prevent bacterias from occupying same cell
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
        # self.x = max(0, min(self.x, GRID_WIDTH - 1))
        # self.y = max(0, min(self.y, GRID_HEIGHT - 1))
        self.x = max(0, min(self.x, (SIM_BOUND_WIDTH - 3) // TILE_SIZE))
        self.y = max(0, min(self.y, (HEIGHT - 1) // TILE_SIZE))

    def chase(self, direction):
        step = max(1, self.legs)
        self.hp -= C_living + math.floor(self.legs/2)
        self.move(direction, step)
    
    # running logic against hungry bacteria
    def run(self, direction):
        # move 1 step in the opposite direction
        opposite_directions = {
            'top': 'down',
            'top_right': 'down_left',
            'right': 'left',
            'down_right': 'top_left',
            'down': 'top',
            'down_left': 'top_right',
            'left': 'right',
            'top_left': 'down_right'
        }
        opposite_direction = opposite_directions.get(direction, 'top')
        step = max(1, self.legs)
        # hp cost too
        self.hp -= C_living + math.floor(self.legs/2)
        self.move(opposite_direction, step)
                        
    def roam(self): # movement pattern ROAM
        # reduce hp as it roams - costs energy to move// remove later
        self.hp -= C_living
        # generate random direction and move
        direction = random.choice(['top', 'top_right', 'right', 'down_right', 'down', 'down_left', 'left', 'top_left'])
        step = 1
        self.move(direction, step)
    
    def frantic(self): # movement pattern ROAM
        # reduce hp as it roams - costs energy to move// remove later
        self.hp -= C_living
        # generate random direction and move
        direction = random.choice(['top', 'top_right', 'right', 'down_right', 'down', 'down_left', 'left', 'top_left'])
        step = 4
        self.move(direction, step)
    
    # death - all can die
    def die(self, bacteria_list):
    # check if HP is below 0, remove the bacteria
        global deaths # access global var
        if self.hp <= 0:
            bacteria_list.remove(self)
            deaths += 1
    
    # absorption logic
    def absorb(self, bacteria_list):
        # set the range
        absorb_range = self.absorb_range
        # check if any other bacteria is within the bite range
        for bacteria in bacteria_list:
            if bacteria != self and abs(self.x - bacteria.x) <= absorb_range and abs(self.y - bacteria.y) <= absorb_range: # only within range
                # case 1 - both BL: only higher absorption will absorb
                if self.HungryOn and bacteria.HungryOn:
                    # sub case: higher absoption will win out
                    if self.absorption > bacteria.absorption:
                        absorb_damage = min(self.absorption*M_absorption*((bacteria.membrane/16)**M_membrane), bacteria.hp)  # set to depend on absorption value (20 is just example); also prevents absorption from regaining more than other bacterias hp
                        if absorb_damage < 1: # if the other guy armor is cracked, deal only 1 dmg
                            absorb_damage = 1
                        self.hp += round(absorb_damage,2)
                        bacteria.hp -= absorb_damage
                # case 2 - self is BL, other is not
                    # lower absorption still allowed
                elif self.HungryOn and not bacteria.HungryOn:
                    absorb_damage = min(self.absorption*M_absorption - bacteria.membrane*M_membrane, bacteria.hp)
                    if absorb_damage < 1: # if the other guy armor is cracked, deal only 1 dmg
                            absorb_damage = 1
                    self.hp += round(absorb_damage,2)
                    bacteria.hp -= absorb_damage

                    # print(f"Bacteria {self.colour_name} bit Bacteria {bacteria.colour_name} at position {bacteria.x},{bacteria.y}.")
                    # print(f"After absorbing: {self.colour_name} HP: {self.hp}, {bacteria.colour_name} HP: {bacteria.hp}")

            # check if the other bacteria's HP is zero after absorption
            # if bacteria.hp <= 0:
                # print(f"Bacteria {bacteria.colour_name} has been fully eaten by Bacteria {self.colour_name}!")
        
    def photosynthesise(self, sunlight_values):
        # bacteria is within the grid boundaries
        if 0 <= self.x < GRID_WIDTH and 0 <= self.y < GRID_HEIGHT:
            # check if there is sunlight in the current cell
            if sunlight_values[self.y][self.x] > 0:
                # check if the bacteria's HP is below its matingHP threshold
                if self.hp < matingHP * self.maxHP:
                    # recover HP based on sunlight value and photosynthesis trait
                    hp_gain = sunlight_values[self.y][self.x] * (self.photosynthesis+1) * M_photosynthesis # will still gain at some hp; multiplier on photosynthesis
                    self.hp += hp_gain
                    # ensure HP doesn't exceed maxHP
                    self.hp = min(self.hp, self.maxHP)
                    # print(f"Bacteria {self.colour_name} at ({self.x}, {self.y}) photosynthesized and gained {hp_gain} HP.")

                    # add light seeking behaviour as well
                    max_sunlight = 0
                    direction_to_move = None

                    # check sunlight values in tendrils
                    for direction, positions in self.tendrils_lines.items():
                        for pos in positions:
                            if 0 <= pos[0] < GRID_WIDTH and 0 <= pos[1] < GRID_HEIGHT:
                                if sunlight_values[pos[1]][pos[0]] > max_sunlight:
                                    max_sunlight = sunlight_values[pos[1]][pos[0]]
                                    direction_to_move = direction
                    
                    # move towards the cell with higher sunlight value
                    if direction_to_move and random.random() < self.photosynthesis / 15:
                        step = max(1, self.legs)
                        self.hp -= math.floor(self.legs / 2)
                        self.move(direction_to_move, step)
                        # print(f"Bacteria {self.colour_name} moved towards higher sunlight in direction {direction_to_move} and consumed {step} HP.")
    
    # mating logic using DNA
    def mate(self, bacteria_list):
        for bacteria in bacteria_list:
            # set the range
            pheromone_range = 2 # can only mate if within 2 cells
            # check if any other bacteria is within mating range
            if bacteria != self and abs(self.x - bacteria.x) <= pheromone_range and abs(self.y - bacteria.y) <= pheromone_range: # only within range
                # both must be in mating mood
                if self.MatingOn and bacteria.MatingOn:
                    # check cooldown before mating
                    current_time = pygame.time.get_ticks()
                    if (current_time - self.last_mate_time >= BCTR_MATING_COOLDOWN) and (current_time - bacteria.last_mate_time >= BCTR_MATING_COOLDOWN):
                        child_dna = self.inherit(self.dna, bacteria.dna)
                        if child_dna == "":
                            # print("mating failed")
                            break
                        else:
                            # create child with inherited traits and DNA
                            child = Bacteria(self.x, self.y, isChild=True, dna = child_dna)
                            # child should spawn where the parents mated
                            child.x = (self.x + bacteria.x) // 2
                            child.y = (self.y + bacteria.y) // 2
                            # # child shd start with half hp - now all bacteria start with half hp
                            # child.hp = 0.5*child.maxHP

                            # append child to bacteria list
                            bacteria_list.append(child)

                            # parents sacrifice % of total hp to create child
                            self.hp -= M_sacrifice*self.maxHP
                            bacteria.hp -= M_sacrifice*bacteria.maxHP

                            # set a timer so that next mating opportunity isnt immediate; curb parent-child mating
                            self.last_mate_time = current_time

                            # print(f"Bacteria {self.colour_name} mated with {bacteria.colour_name} and gave birth to {child.colour_name}")

        self.MatingOn = False
        bacteria.MatingOn = False

    # inheritance logic - to get dna from mate() and pass it to inherit(), which will set the child bacteria new dna
    # use factory method
    @staticmethod
    def inherit(dna1, dna2):
        # step 0: (selection)
        # check both parents dna 1s differ by at most 1
        num_ones1 = dna1.count('1')
        num_ones2 = dna2.count('1')
        ones_difference = abs(num_ones1 - num_ones2)
        if ones_difference > 1:
            # print("parents cannot mate")
            return "" # "Parents cannot mate."
        
        # step 1:
        # turn both DNA strings into lists of how many traits there are with each entry being a value
        dna_trait1 = [int(dna1[i:i+4], 2) for i in range(0, len(dna1), 4)]
        dna_trait2 = [int(dna2[i:i+4], 2) for i in range(0, len(dna2), 4)]

        # step 2: (crossover)
        # find the highest value and its index in each DNA string
        max_values_indices1 = [(val, idx) for idx, val in enumerate(dna_trait1)]
        max_values_indices2 = [(val, idx) for idx, val in enumerate(dna_trait2)]

        max_value1, max_index1 = max(max_values_indices1)
        max_value2, max_index2 = max(max_values_indices2)

        # ff there's a tie in max values, randomly choose one and assign its index
        max_values1 = [val for val, _ in max_values_indices1 if val == max_value1]
        max_values2 = [val for val, _ in max_values_indices2 if val == max_value2]

        if len(max_values1) > 1:
            max_index1 = random.choice([idx for _, idx in max_values_indices1 if _ == max_value1])

        if len(max_values2) > 1:
            max_index2 = random.choice([idx for _, idx in max_values_indices2 if _ == max_value2])

        # handle case where max index of both parents is the same
        if max_index1 == max_index2:
            # find out which one has the higher value
            if max_value1 >= max_value2:
                # keep max dna 1, find next highest for 2nd parents
                max_value2 = max((val for idx, val in enumerate(dna_trait2) if idx != max_index1))
                max_index2 = dna_trait2.index(max_value2)

            else:
                max_value1 = max((val for idx, val in enumerate(dna_trait1) if idx != max_index2))
                max_index1 = dna_trait1.index(max_value1)

        # print("dna1:",max_value1,max_index1+1, "dna2:", max_value2,max_index2+1)

        # step 3:
        # directly copy the DNA strings corresponding to the traits of both parents to the child DNA
        child_dna = ''
        inherited_indices = set()  # store indices of inherited trait segments

        # prioritize traits based on strength, ensuring no tie-breakers
        for i in range(len(dna_trait1)):
            if i == max_index2 and (i != max_index1 or max_value2 > max_value1):
                child_dna += dna2[i*4:i*4+4]
                inherited_indices.add(i)
            elif i == max_index1 and (i != max_index2 or max_value1 > max_value2):
                child_dna += dna1[i*4:i*4+4]
                inherited_indices.add(i)
            else:
                child_dna += '0000'  # placeholder for non-max traits

        # step 4:
        # ensure the number of 1s is at least the max of the parents' number of 1s
        max_ones = max(dna1.count('1'), dna2.count('1'))

        # replace remaining 0s randomly until achieving desired number of 1s (diversity)
        child_ones = child_dna.count('1')
        while child_ones < max_ones:
            zero_positions = [pos for pos, char in enumerate(child_dna) if char == '0']
            if zero_positions:
                random_zero_position = random.choice(zero_positions)
                child_dna = child_dna[:random_zero_position] + '1' + child_dna[random_zero_position+1:]
                child_ones += 1
            else:
                break

        # step 5:
        # 50% chance, add an extra 1 (mutation/evolution)
        if random.random() < 0.5:
            # print("lucky")
            zero_positions = [pos for pos, char in enumerate(child_dna) if char == '0']
            if zero_positions:
                random_zero_position = random.choice(zero_positions)
                child_dna = child_dna[:random_zero_position] + '1' + child_dna[random_zero_position+1:]
                child_ones += 1

        # step 6:
        # ensure that the number of 1s in the child does not exceed MAX_POWER
        if child_ones > BCTR_MAX_POWER:
            print("child is too powerful")
            return "" # "Child is too powerful"

        return child_dna

    # ---- FOR PYGAME SCREEN ----

    # draws main body
    def draw(self, screen):
        # draw body
        pygame.draw.rect(screen, self.colour, (self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # frames for tendril animations
        frame1 = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA, 32)
        frame1.convert_alpha()
        frame1.fill((0, 0, 0, 0))  # transparent bg
        pygame.draw.arc(frame1, self.colour, (0, 0, TILE_SIZE, TILE_SIZE), 0.5 * math.pi, 1.5 * math.pi, 1)

        frame2 = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA, 32)
        frame2.convert_alpha()
        frame2.fill((0, 0, 0, 0))
        pygame.draw.arc(frame2, self.colour, (0, 0, TILE_SIZE, TILE_SIZE), 1.5 * math.pi, 0.5 * math.pi, 1)

        frame3 = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA, 32)
        frame3.convert_alpha()
        frame3.fill((0, 0, 0, 0))
        pygame.draw.arc(frame3, self.colour, (0, 0, TILE_SIZE, TILE_SIZE), 0, math.pi, 1)

        frame4 = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA, 32)
        frame4.convert_alpha()
        frame4.fill((0, 0, 0, 0))
        pygame.draw.arc(frame4, self.colour, (0, 0, TILE_SIZE, TILE_SIZE), math.pi, 2 * math.pi, 1)

        frame5 = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA, 32)
        frame5.convert_alpha()
        frame5.fill((0, 0, 0, 0))
        pygame.draw.arc(frame5, self.colour, (0, 0, TILE_SIZE, TILE_SIZE), 0.25 * math.pi, 1.25 * math.pi, 1)

        frame6 = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA, 32)
        frame6.convert_alpha()
        frame6.fill((0, 0, 0, 0))
        pygame.draw.arc(frame6, self.colour, (0, 0, TILE_SIZE, TILE_SIZE), 1.25 * math.pi, 0.25 * math.pi, 1)

        frame7 = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA, 32)
        frame7.convert_alpha()
        frame7.fill((0, 0, 0, 0))
        pygame.draw.arc(frame7, self.colour, (0, 0, TILE_SIZE, TILE_SIZE), 0.75 * math.pi, 1.75 * math.pi, 1)

        frame8 = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA, 32)
        frame8.convert_alpha()
        frame8.fill((0, 0, 0, 0))
        pygame.draw.arc(frame8, self.colour, (0, 0, TILE_SIZE, TILE_SIZE), 1.75 * math.pi, 0.75 * math.pi, 1)
        
        # draw tendrils & animate
        frame_index = pygame.time.get_ticks() // 500  # toggle frames every x milliseconds
        for direction, positions in self.tendrils_lines.items():
            for index, pos in enumerate(positions):
                if direction == 'top' or direction == 'down':
                    frame = frame1 if (index % 2 == 0 and frame_index % 2 == 1) or (index % 2 == 1 and frame_index % 2 == 0) else frame2
                elif direction == 'right' or direction == 'left':
                    frame = frame3 if (index % 2 == 0 and frame_index % 2 == 1) or (index % 2 == 1 and frame_index % 2 == 0) else frame4
                elif direction == 'top_right' or direction == 'down_left':
                    frame = frame5 if (index % 2 == 0 and frame_index % 2 == 1) or (index % 2 == 1 and frame_index % 2 == 0) else frame6
                elif direction == 'top_left' or direction == 'down_right':
                    frame = frame7 if (index % 2 == 0 and frame_index % 2 == 1) or (index % 2 == 1 and frame_index % 2 == 0) else frame8

                screen.blit(frame, (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE))
        
        # define animation parameters for heartbeat
        animation_duration = 6000  # animation duration in milliseconds
        max_radius = self.absorb_range * TILE_SIZE  # maximum radius of the pulsing circle
        animation_progress = pygame.time.get_ticks() % animation_duration # current state of anim

        # calculate the radius of the pulsing circle based on animation progress
        if animation_progress <= animation_duration / 2:
            # growing phase
            radius = (animation_progress / (animation_duration / 2)) * max_radius
        else:
            # shrinking phase
            radius = ((animation_duration - animation_progress) / (animation_duration / 2)) * max_radius

        # pulsing circle centered at the bacteria's coordinates
        pulsing_color = (255, 255, 255)  # color of the pulsing circle (white)
        pygame.draw.circle(screen, pulsing_color, (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2), int(radius), 1)

        
        # draw absorb range as a circle
        absorb_range = self.absorb_range
        pygame.draw.circle(screen, self.colour, (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2), absorb_range * TILE_SIZE, 2)
        
        # display ID and HP overlayed on top of the main body/coordinate
        font = pygame.font.SysFont(None, 12)
        text_hp = font.render(f"HP: {round(self.hp,2)}", True, WHITE)
        is_child = "Child" if self.isChild else "Not Child"
        text_child = font.render(f"{is_child}", True, WHITE)
        screen.blit(text_hp, (self.x * TILE_SIZE, self.y * TILE_SIZE + TILE_SIZE))
        screen.blit(text_child,(self.x * TILE_SIZE, self.y * TILE_SIZE + 2*TILE_SIZE) )

        # hungry and mating flags
        font2 = pygame.font.SysFont(None, 18)
        if self.HungryOn:
            text_Hungry = font2.render("Hungry", True, RED)
            screen.blit(text_Hungry, (self.x * TILE_SIZE, self.y * TILE_SIZE + 3*TILE_SIZE))
        elif self.MatingOn:
            text_mating = font2.render("Mating", True, BLUE)
            screen.blit(text_mating, (self.x * TILE_SIZE, self.y * TILE_SIZE + 3*TILE_SIZE))
        
        # draw the HP bar over the bacteria object
        self.draw_hp_bar(screen)

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
    
    def draw_hp_bar(self, screen):
        # width of the HP bar (pixels)
        bar_width = 50 # shd be always 50px wide - if see long bars cnfm self.hp not capped at self.maxHP
        hp_bar_width = int((self.hp / self.maxHP) * bar_width)

        # color of the HP bar based on the HP level; follow thresholds
        if self.hp > self.maxHP*matingHP:
            hp_color = GREEN
        elif self.hp > self.maxHP*bloodHP:
            hp_color = YELLOW
        else:
            hp_color = RED

        # position of the HP bar within the grid cell
        grid_cell_x = self.x * TILE_SIZE  # convert grid cell coordinate to pixel coordinate
        grid_cell_y = self.y * TILE_SIZE

        # relative to the grid cell
        hp_bar_x = grid_cell_x + (TILE_SIZE - bar_width) // 2
        hp_bar_y = grid_cell_y - 10  # Adjusted position above the grid cell

        # draw the HP bar
        pygame.draw.rect(screen, BLACK, [hp_bar_x, hp_bar_y, bar_width, 5])
        pygame.draw.rect(screen, hp_color, [hp_bar_x, hp_bar_y, hp_bar_width, 5])

    # ---- END OF PYGAME SCREEN FUNCTIONS ----
            
# ---- ---- ---- ---- end of BACTERIA class ---- ---- ---- ----

####

# ---- ---- ---- ---- ANALYTICS code ---- ---- ---- ----

# update_graph function saves the plot as an image file and then load it using pygame

def update_graph(bacteria_count_history, deaths_history, avg_trait_history, avg_lifespan_history, avg_power_history):
    plt.clf()  # clear the previous plot
    plt.figure(figsize=(5, 10))
    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9, wspace=0.1, hspace=0.1)

    # plot bacteria count over time
    plt.subplot(4, 1, 1)
    plt.plot(bacteria_count_history, color='blue')
    plt.title('Bacteria Count Over Time', fontsize=8)
    plt.xlabel('Time Step', fontsize=8)
    plt.ylabel('Bacteria Count', fontsize=8)
    plt.axhline(y=sim_num_bact, color='gray', linestyle='--', label=f'Starting Count: {sim_num_bact}')
    # add the current bacteria count as a dot at the most recent point
    current_bacteria_count = len(bacteria_list)
    plt.scatter(len(bacteria_count_history) - 1, current_bacteria_count, color='red',
                label=f'Current Bacteria Count: {current_bacteria_count}')
    plt.legend(loc="upper left", fontsize=7)
    plt.grid(True)
    plt.gca().tick_params(axis='both', which='major', labelsize=6)

    # plot death count over time
    plt.subplot(4, 1, 2)
    plt.plot(deaths_history, color='red')
    plt.title('Deaths Over Time', fontsize=8)
    plt.xlabel('Time Step', fontsize=8)
    plt.ylabel('Deaths', fontsize=8)
    # add the current death count as a dot at the most recent point
    current_deaths = deaths
    plt.scatter(len(deaths_history) - 1, current_deaths, color='blue', label=f'Current Death Count: {current_deaths}')
    plt.legend(loc="upper left", fontsize=7)
    plt.grid(True)
    plt.gca().tick_params(axis='both', which='major', labelsize=6)

    # plot average traits over time
    plt.subplot(4, 1, 3)
    for trait, history in avg_trait_history.items():
        plt.plot(history, label=f'Average {trait.capitalize()}: {round(history[-1], 2)}')
    plt.plot(avg_power_history, label='Average Power', color='grey')  # Add the average power curve
    plt.title('Average Traits Over Time', fontsize=8)
    plt.xlabel('Time Step', fontsize=8)
    plt.ylabel('Trait Value', fontsize=8)
    current_avg_power = avg_power_history[-1] if avg_power_history else 0
    plt.scatter(len(avg_power_history) - 1, current_avg_power, color='gray',
                label=f'Current Average Power: {round(current_avg_power, 2)}')
    plt.legend(loc="upper left", fontsize=7)
    plt.grid(True)
    plt.gca().tick_params(axis='both', which='major', labelsize=6)

    # plot average lifespan over time
    plt.subplot(4, 1, 4)
    plt.plot(avg_lifespan_history, color='black')
    plt.title('Average Lifespan Over Time', fontsize=8)
    plt.xlabel('Time Step', fontsize=8)
    plt.ylabel('Lifespan', fontsize=8)
    # add the current average lifespan as a dot at the most recent point
    current_avg_lifespan = avg_lifespan_history[-1] if avg_lifespan_history else 0
    plt.scatter(len(avg_lifespan_history) - 1, current_avg_lifespan, color='gray',
                label=f'Average Bacteria Lifespan: {round(current_avg_lifespan, 2)}')
    plt.legend(loc="upper left", fontsize=7)
    plt.grid(True)
    plt.gca().tick_params(axis='both', which='major', labelsize=6)

    # adjust layout to prevent overlap
    plt.tight_layout()

    # save the plot as an image file
    plot_filename = "plot.png"
    plt.savefig(plot_filename)

    # load the saved image using Pygame
    plot_surface = pygame.image.load(plot_filename)

    # remove the image file
    os.remove(plot_filename)

    # blit the plot onto the Pygame screen
    screen.blit(plot_surface, (SIM_BOUND_WIDTH, 0))

    # updates time step
    pygame.display.update()

    # prevents many plots from opening up
    plt.close()

# ---- ---- ---- ---- end of ANALYTICS code ---- ---- ---- ----

####

# ---- ---- ---- ---- main PYGAME LOOP setup ---- ---- ---- ---- 
screen = pygame.display.set_mode( (WIDTH,HEIGHT) ) #takes in a tuple as argument; not 2 numbers
clock = pygame.time.Clock()

# define global variables for game
bacteria_list = []
deaths = 0

# draw bounding box for bacteria simulation
def draw_outline():
    pygame.draw.rect(screen, GREY, (0, 0, SIM_BOUND_WIDTH, HEIGHT), 4)

# ---- main pygame simulation loop ----

def run_simulation():
    global bacteria_list, deaths, MAX_DATA_POINTS
    INIT_NUM_BACTERIA = sim_num_bact

    bacteria_count_history = []
    deaths_history = []
    avg_trait_history = {'tendrils': [], 'absorption': [], 'membrane': [], 'photosynthesis': [], 'legs': [], 'maxHP': []}
    avg_lifespan_history = []
    avg_power_history = []
    
    # flag to stop graph
    update_graph_flag = True
    
    running = True

    # create initial bacteria
    for _ in range(INIT_NUM_BACTERIA):
        x = random.randint(0, SIM_BOUND_WIDTH//TILE_SIZE - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        bacteria_list.append(Bacteria(x, y))
    
    # initialize_plot()
    
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            # pygame.QUIT is a value, pygame.quit() is a function call (the X button)
            # this enables the CLOSE button to work
            if event.type == pygame.QUIT:
                running = False
        
        # define the pygame screen        
        screen.fill(WHITE) # white BG but doesnt rly matter
        draw_sun() # draw sunlight grid
        draw_outline() # draw outline of simulation module

        # draw and move bacteria 
        for bacteria in bacteria_list:
            bacteria.draw(screen)
            bacteria.live(bacteria_list) # --- to encapsulate all actions into 1 function eg .live()
            bacteria.update_tendrils_lines()
            bacteria.die(bacteria_list)
        
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

        # real time update to average traits and lifespan
        if len(bacteria_list) > 0:
            total_traits = {'tendrils': 0, 'absorption': 0, 'membrane': 0, 'photosynthesis': 0, 'legs': 0, 'maxHP': 0}
            total_lifespan = 0
            total_power = 0

            for bacteria in bacteria_list:
                total_lifespan += bacteria.lifespan
                total_power += sum(x.count('1') for x in bacteria.dna)
                for trait, value in bacteria.traits.items():
                    total_traits[trait] += value

            num_bacteria = len(bacteria_list)
            avg_trait_values = {trait: total_traits[trait] / num_bacteria for trait in total_traits}
            avg_lifespan = total_lifespan / num_bacteria
            avg_power = total_power / num_bacteria

            # append average trait values and lifespan to their respective history lists
            for trait, value in avg_trait_values.items():
                avg_trait_history[trait].append(value)
            avg_lifespan_history.append(avg_lifespan)
            avg_power_history.append(avg_power)

        # limit history lists to a maximum number of data points
        if len(bacteria_count_history) > MAX_DATA_POINTS:
            bacteria_count_history = bacteria_count_history[-MAX_DATA_POINTS:]
        if len(deaths_history) > MAX_DATA_POINTS:
            deaths_history = deaths_history[-MAX_DATA_POINTS:]

        # update the graph if flag is true and bacteria list is not empty
        if update_graph_flag and len(bacteria_list) > 0:
            # update plot
            update_graph(bacteria_count_history, deaths_history, avg_trait_history, avg_lifespan_history, avg_power_history)

        # stop updating graph if bacteria list is empty
        if len(bacteria_list) == 0:
            update_graph_flag = False
        
        # print last alive
        if len(bacteria_list) == 1:
            print(bacteria_list[0].dna, bacteria_list[0].traits)

        # updates time step
        pygame.display.update()
        
        # time step values
        time_steps = list(range(1, len(bacteria_count_history) + 1))

        # dictionary with the data
        data = {
            'Time_Step': time_steps,
            'Bacteria_Count': bacteria_count_history,
            'Deaths': deaths_history,
            'Average_Lifespan': avg_lifespan_history,
            'Average_Power': avg_power_history
        }

        # columns for average traits
        for trait, history in avg_trait_history.items():
            data[f'Average_{trait.capitalize()}'] = history

        # make the df
        df = pd.DataFrame(data)

    pygame.quit()

    # save df as excel file
    excel_filename = f"simulation_data.xlsx"
    df.to_excel(excel_filename, index=False)

if __name__ == "__main__":
    run_simulation()

# ---- ---- ---- ---- end of PYGAME LOOP ---- ---- ---- ---- 