import numpy as np
import pandas as pd
import random
import simpy

# Parameters - Passengers
PAS_ARRIVAL_MEAN = 5
PAS_NUMBER_MEAN = 500
PAS_NUMBER_STD = 100

ONLINE_CHECKIN_RATIO_MEAN = 0.6
GROUP_SIZE_MEAN = 2.25
GROUP_SIZE_STD = 0.50

TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN = 0.5
TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD = 0.25
TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN = 0.5
TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD = 0.25

TIME_TO_WALK_TO_IMMIG_MEAN = 0.5
TIME_TO_WALK_TO_IMMIG_STD = 0.1

TIME_TO_WALK_TO_SEC_MEAN = 0.5
TIME_TO_WALK_TO_SEC_STD = 0.1

TIME_TO_WALK_TO_BOARD_MEAN = 0.5
TIME_TO_WALK_TO_BOARD_STD = 0.1

ONLINE_CHECKIN_LINES = 5
ONLINE_CHECKIN_CUST_PER_LINE = 1
ONLINE_CHECKIN_MEAN = 2
ONLINE_CHECKIN_STD = 0.2

OFFLINE_CHECKIN_LINES = 5
OFFLINE_CHECKIN_CUST_PER_LINE = 1
OFFLINE_CHECKIN_MEAN = 2
OFFLINE_CHECKIN_STD = 0.2

IMMIG_LINES = 5
IMMIG_CUST_PER_LINE = 1
IMMIG_MEAN = 5
IMMIG_STD = 0.5

SEC_LINES = 10
SEC_CUST_PER_LINE = 1
SEC_MEAN = 5
SEC_STD = 0.5

BOARD_LINES = 1
BOARD_CUST_PER_LINE = 1
BOARD_MEAN = 2
BOARD_STD = 0.5

# Parameters - Airplane
RANDOM_SEED = 42
num_airplane = 5
time_interval = 15
NUM_RUNWAY = 1    # Number of runway in the airport
TAKEOFFTIME = 5   # Minutes airplane takes to take off
LANDTIME = 6      # Minutes airplane takes to land
DEPARTURE_INTER = 10  # Create departure airplane every 10 minutes
LAND_INTER = 10      # Create land airplane every 10 minutes
AIRPLANE_CAPACITY = 200 # airplane capacity is 200
TIME_ON_GROUND = 45 #Arrival aircraft spends 45 minutes at the terminal for de-boarding and boarding (this doesn't include departure schedule)
AIRPLANES_AT_TERMINAL = 5 #Total aircrafts present at the termianl at the start of the simulation
AIRPLANES_SCHEDULED_TO_LAND_TODAY = 10 #Total aircrafts expected to arrive and land today at the airport

# Global Dictionary
passenger_dict = dict()
# stores plane id as key and the list passenger id who completed boarding as values


# pygame parameters

# pygame.init()
# screen = pygame.display.set_mode((1280, 960), 0, 32)
# points = []
# my_font = pygame.font.SysFont("arial", 20)

# Edit 3 - Matching with Hui's code

# defining seperate classes for resources
# Passenger simulation model

class Passenger(object):
    def __init__(self, env, pass_id, plane_id):
        self.env = env
        self.pass_id = pass_id
        self.plane_id = plane_id
        self.checkin = False
        self.immig = False
        self.security = False
        self.boarding = False
        print("Passenger Created with id %d and plane id %d" %(pass_id, plane_id))

    def schedule(self, time, pf):
        print("Passenger with id %d and plane id %d scheduled" %(self.pass_id, self.plane_id))
        yield env.timeout(time)
        a = random.random()
        if a > ONLINE_CHECKIN_RATIO_MEAN:
            self.env.process(pf.on_checkin_process(self))
        else:
            self.env.process(pf.off_checkin_process(self))

        
class Passenger_Flow(object):
    def __init__(self, env):
        self.env = env
        self.online_checkin_lines = [simpy.Resource(env, capacity = ONLINE_CHECKIN_CUST_PER_LINE) for _ in range(ONLINE_CHECKIN_LINES)]
        self.offline_checkin_lines = [simpy.Resource(env, capacity = OFFLINE_CHECKIN_CUST_PER_LINE) for _ in range(OFFLINE_CHECKIN_LINES)]
        self.immig_lines = [simpy.Resource(env, capacity = IMMIG_CUST_PER_LINE) for _ in range(IMMIG_LINES)]
        self.sec_lines = [simpy.Resource(env, capacity = SEC_CUST_PER_LINE) for _ in range(SEC_LINES)]
        self.board_lines = [simpy.Resource(env, capacity = BOARD_CUST_PER_LINE) for _ in range(BOARD_LINES)]
        
    def shortest_line(self, lines):
        # this function is to pick the shortest line 
        # return the index of the shortest line among the resources
        shuffled = list(zip(range(len(lines)), lines)) # tuples of (i, line)
        random.shuffle(shuffled)
        shortest = shuffled[0][0]
        for i, line in shuffled:
            if len(line.queue) < len(lines[shortest].queue):
                shortest = i
                break
        return shortest      
    
    def on_checkin_process(self, passenger):
        # time to walk
        
        print("online checkin walk start: ", env.now)
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN, TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD)))
        print("online checkin walk end: ", env.now)
        # time to process
        index = self.shortest_line(self.online_checkin_lines)
        print("Online checkin started for passeger %d of plane %d at line %d" %(passenger.pass_id, passenger.plane_id, index+1))
        with self.online_checkin_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(ONLINE_CHECKIN_MEAN, ONLINE_CHECKIN_STD)))
            print("Online checkin completed for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
            passenger.checkin = True
        self.env.process(self.immig_process(passenger))
                
    def off_checkin_process(self, passenger):
        # time to walk
        print("offline checkin walk start: ", env.now)
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN, TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD)))
        print("offline checkin walk end: ", env.now)
        # time to process
        index = self.shortest_line(self.offline_checkin_lines)
        print("Offline checkin started for passeger %d of plane %d at line %d" %(passenger.pass_id, passenger.plane_id, index+1))
        with self.offline_checkin_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(OFFLINE_CHECKIN_MEAN, OFFLINE_CHECKIN_STD)))
            print("Offline completed for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
            passenger.checkin = True
        self.env.process(self.immig_process(passenger))
    
    def immig_process(self, passenger):
        # time to walk
        print("Immigration started for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
        print("immig process walk start: ", env.now)
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_IMMIG_MEAN, TIME_TO_WALK_TO_IMMIG_STD)))
        print("immig process walk start: ", env.now)
        # time to process
        index = self.shortest_line(self.immig_lines)
        with self.immig_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(IMMIG_MEAN, IMMIG_STD)))
            print("Immigration checkin completed for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
            passenger.immig = True
        self.env.process(self.sec_process(passenger))

    def sec_process(self, passenger):
        # time to walk
        print("Security check started for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
        print("security check walk start: ", env.now)
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_SEC_MEAN, TIME_TO_WALK_TO_SEC_STD)))
        print("security check walk end: ", env.now)
        # time to process
        index = self.shortest_line(self.sec_lines)
        with self.sec_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(SEC_MEAN, SEC_STD)))
            print("Security check completed for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
            passenger.security = True
        self.env.process(self.board_process(passenger))
            
    def board_process(self, passenger):
        # time to walk
        print("Boarding started for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
        print("boarding walk start: ", env.now)
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_BOARD_MEAN, TIME_TO_WALK_TO_BOARD_STD)))
        print("boarding walk end: ", env.now)
        # time to process
        index = self.shortest_line(self.board_lines)
        with self.board_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(BOARD_MEAN, BOARD_STD)))
            print("Boarding completed for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
            passenger.boarding = True
        passenger_dict[passenger.plane_id].append(passenger.pass_id)

# Airplane flow model

class Runnway(object):
    def __init__(self, env, num_runway):
        self.env = env
        self.runway = simpy.Resource(env, num_runway)

    def occupy(self, occupy_time): #function indicating whether runway is occupied or idle
        yield self.env.timeout(occupy_time)


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
    def __init__(self, env, num_airplane, time_interval, runway, pf):
        self.num_airplane = num_airplane
        self.time_interval = time_interval
        self.runway = runway
        self.pf = pf
        self.airplanes = []
        self.passengers = []
    
    def schedule(self):
        #yield env.timeout(self.time_interval)
        for i in range(self.num_airplane):
            airplane = Airplane(env, 'Depart_airplane %d' % i, self.runway, TAKEOFFTIME, LANDTIME)
            self.airplanes.append(airplane)
            env.process(airplane.schedule( (i * self.time_interval) + 120))
            pass_num = round(abs(random.gauss(PAS_NUMBER_MEAN,PAS_NUMBER_STD)))
            for j in range(pass_num):
                passenger = Passenger(env, j+1, i+1)
                self.passengers.append(passenger)
                env.process(passenger.schedule(i * self.time_interval, self.pf))

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
    pf = Passenger_Flow(env)
    departure_Table = Departure_Table(env, 10, 15, runway, pf)
    env.process(departure_Table.schedule())
    land_Table = Land_Table(env, 10, 15, runway)
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
# print('Airport Runway Traffic Simulation')
# random.seed(RANDOM_SEED)  # This helps reproducing the results

# # Create an environment and start the setup process
# env = simpy.Environment()
# env.process(ATF(env))

# # Execute!
# env.run(10000)



# Tesing the simulation with sample passenger creation

def test(env):
    passenger = Passenger(env, 3, 5)
    pf = Passenger_Flow(env)
    time_interval = 15
    yield env.process(passenger.schedule(time_interval, pf))
    passenger = Passenger(env, 5, 6)
    yield env.process(passenger.schedule(time_interval, pf))

def test2(env):
    runway = Runnway(env, NUM_RUNWAY) #Creating runway object
    pf = Passenger_Flow(env)
    airplanes = []
    passengers = []
    for i in range(num_airplane):
        #print("passenger dictionary",passenger_dict)
        airplane = Airplane(env, 'Depart_airplane %d' % i, runway, TAKEOFFTIME, LANDTIME)
        airplanes.append(airplane)
        passenger_dict[i+1] = []
        pass_num = round(abs(random.gauss(PAS_NUMBER_MEAN,PAS_NUMBER_STD)))
        for j in range(pass_num):
            passenger = Passenger(env, j+1, i+1)
            passengers.append(passenger)
            yield env.process(passenger.schedule((i*time_interval),pf))
        yield env.process(airplane.schedule( (i * time_interval) + 120))

print('Airport Runway Traffic Simulation')
random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(test2(env))

# Execute!
env.run(20000)


print(passenger_dict)
