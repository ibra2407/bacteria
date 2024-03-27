# install these libraries
import pygame
import random
import math

# initialise a pygame instance
pygame.init()

# pygame screen elements
WIDTH, HEIGHT = 300,300 # default 800,800
TILE_SIZE = 10
GRID_WIDTH = WIDTH // TILE_SIZE
GRID_HEIGHT = HEIGHT // TILE_SIZE
FPS = 10 # clock ticks {FPS} times a real second

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

    # BACTERIA SIMULATION PARAMS; access in class functions as Bacteria.----
    EXISTING_IDS = set()  # store generated IDs, ensuring they dont repeat
    START_POWER = 8 # number of 1s allowed in dna string at the start; "power" of each cell at the start shd be low and get higher as generations go
    # can start with half of 24 (total)
    MAX_POWER = 18 # can only choose to max out 4 out of 6 traits; 10% chance of a child to increase its power
    
    # insert others to change "global" params for all bacteria

    def __init__(self, x, y, isChild = False):

        # current coordinate
        self.x = x
        self.y = y

        # lifespan to measure life
        self.lifespan = 0

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
            self.dna = 24*"0"

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

        self.hp = max(200, self.traits['maxHP']*200) # start with 80% hp so dont spawn in mating mood
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

        # # HP > 70%; definitely wants to mate
        # self.MatingOn = True
        # # finds a mate
        if(self.hp > 0.8*self.maxHP):
            self.MatingOn = True
            self.BloodlustOn = False

        # # HP 30-70%
        if (self.hp > 0.3*self.maxHP and self.hp <= 0.8*self.maxHP):
            if prob_hunt > 0.9:
                self.BloodlustOn = True
                self.MatingOn = False
            if prob_mate > 0.9:
                self.BloodlustOn = False
                self.MatingOn = True
            if prob_movement > 0.6: # might require balancing
                self.BloodlustOn = False
                self.MatingOn = False

        # # HP < 30%; definitely wants to hunt
        # self.BloodlustOn = True
        if self.hp <= 0.3*self.maxHP:
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
                            print(f"Bacteria {self.colour_name} is on the chase for bacteria {bacteria.colour_name}")
                            self.chase(direction)

                            # hunting case
                            if self.BloodlustOn:
                                self.absorb(bacteria_list)
                            
                            # mating case
                            if self.MatingOn:
                                if prob_mate > 0.9:
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
            print(f"collision at {self.x},{self.y}")
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
            'traits': self.traits
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
        pheromone_range = 4
        one_child = 0
        for bacteria in bacteria_list:
            # check if any other bacteria is within mating range
            if bacteria != self and abs(self.x - bacteria.x) <= pheromone_range and abs(self.y - bacteria.y) <= pheromone_range: # only within range
                # both must be in mating mood
                if self.MatingOn and bacteria.MatingOn:
                    # Identify highest trait values for both parents
                    self_highest_trait = max(self.traits.items(), key=lambda x: x[1])
                    other_highest_trait = max(bacteria.traits.items(), key=lambda x: x[1])

                    # Child inherits both parents' strongest traits
                    child_traits = {self_highest_trait[0]: self_highest_trait[1], other_highest_trait[0]: other_highest_trait[1]}

                    # Calculate total number of 1s in parents' DNA
                    total_ones_self = self.dna.count('1')
                    total_ones_other = bacteria.dna.count('1')

                    # Determine number of 1s in child's DNA
                    child_total_ones = max(total_ones_self, total_ones_other)
                    # There's a 10% chance for an extra 1 in child's DNA
                    if random.uniform(0, 1) < 0.1:
                        child_total_ones += 1

                    # Ensure child_total_ones does not exceed MAX_POWER
                    child_total_ones = min(child_total_ones, Bacteria.MAX_POWER)

                    # Allocate remaining 1s randomly while maintaining total_ones
                    child_dna = ''.join(['1' if i < child_total_ones else '0' for i in range(child_total_ones)])

                    # Create child with inherited traits and DNA
                    child = Bacteria(self.x, self.y, isChild=True)
                    child.dna = child_dna
                    # Child should spawn where the parents mated
                    child.x = (self.x + bacteria.x) // 2
                    child.y = (self.y + bacteria.y) // 2

                    if one_child == 0:
                        # Append child to bacteria list
                        bacteria_list.append(child)
                    one_child = 1
        self.MatingOn = False
        bacteria.MatingOn = False

    # inheritance logic - to get dna from mate() and pass it to inherit(), which will set the child bacteria new dna
    def inherit(self, parent1, parent2):
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

# list to store bacteria objects and their lifespan
bacteria_lifespan = {}

# function to update bacteria lifespan at each time step
def update_bacteria_lifespan(bacteria_list):
    for bacteria in bacteria_list:
        bacteria.lifespan += 1

# global variable setup for game to work
bacteria_list = []
deaths = 0

# main pygame program
def main():
    global bacteria_list
    INIT_NUM_BACTERIA = 2
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
        font3 = pygame.font.SysFont(None, 24)  # define font
        # population count
        bacteria_count_text = font3.render(f"Bacteria count: {len(bacteria_list)}", True, WHITE)  # render text
        screen.blit(bacteria_count_text, (10, 10))  # hard coded coordinates for placement of text

        # death count
        deaths_count = font3.render(f"Death count: {deaths}", True, WHITE)
        screen.blit(deaths_count, (200,10))

        # end of sim status
        if len(bacteria_list) == 0:
            # sort bacteria by lifespan
            sorted_bacteria = sorted(bacteria_lifespan.items(), key=lambda x: x[1]['lifespan'], reverse=True)
            
            # define font for displaying text on screen
            font3 = pygame.font.SysFont(None, 24)

            # display rankings
            y_offset = 100
            ranking_text = font3.render("Ranking of Bacteria:", True, WHITE)
            screen.blit(ranking_text, (10, y_offset))

            for i, (bacteria_id, details) in enumerate(sorted_bacteria):
                text = font3.render(f"Rank {i+1}: Bacteria ID {bacteria_id}, DNA: {details['dna']}, Lifespan: {details['lifespan']} time steps", True, WHITE)
                screen.blit(text, (10, y_offset + (i+1) * 20))

            # display champion
            champion_id, champion_details = sorted_bacteria[0]
            text_dna = font3.render(f"DNA of the champion bacteria: {champion_details['dna']}", True, WHITE)
            screen.blit(text_dna, (10, y_offset + (len(sorted_bacteria) + 2) * 20))

            traits_text = font3.render("Trait values:", True, WHITE)
            screen.blit(traits_text, (10, y_offset + (len(sorted_bacteria) + 3) * 20))
            for i, (trait, value) in enumerate(champion_details['traits'].items()):
                text_trait = font3.render(f"{trait}: {value}", True, WHITE)
                screen.blit(text_trait, (10, y_offset + (len(sorted_bacteria) + 4 + i) * 20))

        # updates time step
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()