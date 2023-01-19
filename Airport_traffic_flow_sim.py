import simpy
import random

import pygame
from pygame.locals import *

# parameters
RANDOM_SEED = 42
NUM_RUNWAY = 1    # Number of runway in the airport
TAKEOFFTIME = 5   # Minutes airplane takes to take off
LANDTIME = 6      # Minutes airplane takes to land
DEPARTURE_INTER = 10  # Create departure airplane every 10 minutes
LAND_INTER = 10      # Create land airplane every 10 minutes
AIRPLANE_CAPACITY = 200 # airplane capacity is 200
TIME_ON_GROUND = 45 #Arrival aircraft spends 45 minutes at the terminal for de-boarding and boarding (this doesn't include departure schedule)
AIRPLANES_AT_TERMINAL = 5 #Total aircrafts present at the termianl at the start of the simulation
AIRPLANES_SCHEDULED_TO_LAND_TODAY = 10 #Total aircrafts expected to arrive and land today at the airport


# pygame parameters

pygame.init()
screen = pygame.display.set_mode((1280, 960), 0, 32)
points = []
my_font = pygame.font.SysFont("arial", 20)

# 需要一个数组来表示排队的飞机数目吧
class Runnway(object):
    def __init__(self, env, num_runway):
        self.env = env
        self.runway = simpy.Resource(env, num_runway)

    def occupy(self, occupy_time): #function indicating whether runway is occupied or idle
        yield self.env.timeout(occupy_time)


class Airplane(object):
    def __init__(self, env, name, rw, takeoff_time, land_time):
        self.env = env
        self.rw = rw
        self.name = name
        self.takeoff_time = takeoff_time
        self.land_time = land_time
        self.passager = 180 #90% capacity
        self.late = False #check if the airplane is late (default is False)
        self.status = False #Status of Takeoff
        
    def takeOff(self):
        self.status = True
        print('%s ready to take off at %.2f.' % (self.name, env.now))
        with self.rw.runway.request() as request:
            yield request
            print('%s enters the runway at %.2f.' % (self.name, env.now))
            yield env.process(self.rw.occupy(self.takeoff_time))
            print('%s leaves the Airport at %.2f.' % (self.name, env.now))
        
    def land(self):
        print('%s ready to land %.2f.' % (self.name, env.now))
        with self.rw.runway.request() as request:
            yield request
            print('%s enters the runway at %.2f.' % (self.name, env.now))
            yield env.process(self.rw.occupy(self.land_time))
            print('%s leaves the runway at %.2f. and enters the terminal' % (self.name, env.now))
            self.status = True
        
        yield env.timeout(TIME_ON_GROUND)
        with self.rw.runway.request() as request:
            yield request
            print('%s leaves the terminal and enters the runway at %.2f.' % (self.name, env.now))
            yield env.process(self.rw.occupy(self.takeoff_time))
            print('%s leaves the Airport at %.2f.' % (self.name, env.now))


    def schedule(self, time):
        yield env.timeout(time)
        # Skip if the plane has already taken off
        if self.status:
            pass
        # Only those with more than 180 boardings are allowed to take off
        if self.passager >= 180:
            # ready to take off 
            env.process(self.takeOff())
        else:
            print('%s late at %.2f.' % (self.name, env.now))
            self.late = True
            
    def boarding(self, passager_num):
        if self.passager < 200:
            self.passager += passager_num

# Schedule the flight departure time
class Departure_Table(object):
    def __init__(self, env, num_airplane, time_interval, runway):
        self.num_airplane = num_airplane
        self.time_interval = time_interval
        self.runway = runway
        self.airplanes = []
    
    def schedule(self):
        for i in range(self.num_airplane):
            airplane = Airplane(env, 'Depart_airplane %d' % i, self.runway, TAKEOFFTIME, LANDTIME)
            self.airplanes.append(airplane)
            env.process(airplane.schedule( i * self.time_interval))

# Schedule the flight land time
class Land_Table(object):
    def __init__(self, env, num_airplane, time_interval, runway):
        self.num_airplane = num_airplane
        self.time_interval = time_interval
        self.runway = runway
        self.airplanes = []
    
    def schedule(self):
        for i in range(self.num_airplane):
            yield env.timeout(self.time_interval)
            airplane = Airplane(env, 'Land_airplane %d' % i, self.runway, TAKEOFFTIME, LANDTIME)
            self.airplanes.append(airplane)
            env.process(airplane.land())


def ATF(env):
    runway = Runnway(env, NUM_RUNWAY) #Creating runway object
    
    departure_Table = Departure_Table(env, 100, 15, runway)
    departure_Table.schedule()
    
    land_Table = Land_Table(env, 100, 15, runway)
    env.process(land_Table.schedule())
    
    while True:

        print(f'{runway.runway.count} of {runway.runway.capacity} slots are allocated.')
        print(f'  Users: {runway.runway.users}')
        print(f'  Queued events: {len(runway.runway.queue)}')
                
        # pygame code
        for event in pygame.event.get():
          if event.type == QUIT:
              exit()

        screen.fill((255,255,255))
        
        # ATF queue line
        pygame.draw.line(screen,(0,0,0),(200, 600),(800,600),3)
        pygame.draw.line(screen,(0,0,0),(200, 640),(800,640),3)

        # rect represent runway 
        #  1 => occupied  0 => idle
        if runway.runway.count == 0:
          pygame.draw.rect(screen, (0,0,0), (880, 570, 100, 100), 3)
        else:
          pygame.draw.rect(screen, (255,0,0), (880, 570, 100, 100))

        # text
        text_surface = my_font.render("ATF queue system", True, (0,0,0), (255, 255, 255))
        screen.blit(text_surface, (430, 580))

        text_surface2 = my_font.render("Runnway", True, (0,0,0), (255, 255, 255))
        screen.blit(text_surface2, (880, 540))

        # draw circle
        # init position x 220 y 620
        x_init = 220
        y_init = 620
        for i in range(len(runway.runway.queue)):
          pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
          x_init = x_init + 40

        pygame.display.update()

        # simpy code
        # Every 1 time step, check whether the flights that are not on time can take off
        yield env.timeout(1)
        for plane in departure_Table.airplanes:
            if plane.status == False:
                if plane.late and plane.passager > 180:
                    env.process(plane.takeOff())
        
# Setup and start the simulation
print('Airport Runway Traffic Simulation')
random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(ATF(env))

# Execute!
env.run(10000)