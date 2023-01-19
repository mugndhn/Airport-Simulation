from cProfile import run
import numpy as np
import pandas as pd
import random
import simpy
import math
import pygame
from pygame.locals import *

import matplotlib.pyplot as plt
# import seaborn as sns
import pandas as pd
# sns.set_theme()


# Parameters - Airplane

TIME_TO_TAKE_OFF = 450
TIME_TO_LAND = 450
PASSENGERS_PER_AIRPLANES = 200      # plane passenger capacity
PASSENGERS_NEED_TO_TAKE_OFF = 190   # how many passenger need to take off 
AIRPLANE_TAKE_OFF_INTERVAL = 900   # Time difference between two consecutive planes
GRACE_PERIOD = 2400           # the time that the plane waits for late passengers
NUM_RUNWAY = 1                      # number of runway in the airport
TIME_ON_GROUND = 2700               # Arrival aircraft spends 45 minutes at the terminal for de-boarding and boarding (this doesn't include departure schedule)
NO_OF_FLIGHTS_PER_DAY = 20		# No of flights per day

# Parameters - Passengers
PTP = 2
ONLINE_CHECKIN_RATIO_MEAN = 0.5  #Control the proportion of passengers using online and offline checkin. 1 means all offline

TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN = 5*PTP 
TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD = 2.5*PTP 
TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN = 5*PTP 
TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD = 2.5*PTP 

TIME_TO_WALK_TO_IMMIG_MEAN = 5*PTP 
TIME_TO_WALK_TO_IMMIG_STD = 1*PTP 

TIME_TO_WALK_TO_SEC_MEAN = 5*PTP 
TIME_TO_WALK_TO_SEC_STD = 1*PTP 

TIME_TO_WALK_TO_BOARD_MEAN = 5*PTP 
TIME_TO_WALK_TO_BOARD_STD = 1*PTP 

ONLINE_CHECKIN_LINES = 10
ONLINE_CHECKIN_CUST_PER_LINE = 1
ONLINE_CHECKIN_MEAN = 45*PTP 
ONLINE_CHECKIN_STD = 2*PTP 

OFFLINE_CHECKIN_LINES = 10
OFFLINE_CHECKIN_CUST_PER_LINE = 1
OFFLINE_CHECKIN_MEAN = 45*PTP 
OFFLINE_CHECKIN_STD = 2*PTP 

IMMIG_LINES = 10
IMMIG_CUST_PER_LINE = 1
IMMIG_MEAN = 30*PTP 
IMMIG_STD = 5*PTP 

SEC_LINES = 10
SEC_CUST_PER_LINE = 1
SEC_MEAN = 30*PTP 
SEC_STD = 5*PTP 

BOARD_LINES = NO_OF_FLIGHTS_PER_DAY
BOARD_CUST_PER_LINE = 1
BOARD_MEAN = 45*PTP 
BOARD_STD = 4*PTP 

# Global Dictionary
passenger_dict = dict()
airplane_dict = dict()

#Parameters - Delays and Cancellations
random.seed(123)
my_list = [0,1,2] # 0 denotes on time, 1 denotes delay and 2 denotes cancelled flight
random_delay_cancel = random.choices(my_list, weights=[80,10,10], k=NO_OF_FLIGHTS_PER_DAY+1)
global delay_index
delay_index = 0
print(random_delay_cancel)


# Parameters for plotting
time_queue = []
online_queue = []
offline_queue = []
immig_queue = []
sec_queue = []
board_queue = []
runway_queue = []

# pygame parameters
pygame.init()
screen = pygame.display.set_mode((1280, 960), 0, 32)
points = []
my_font = pygame.font.SysFont("arial", 20)

class Passenger(object):
    def __init__(self, env, pass_id, plane_id):
        self.env = env
        self.pass_id = pass_id
        self.plane_id = plane_id

    def schedule(self, scheduled_time, pf):
        #print("Passenger with id %d and plane id %d scheduled" %(self.pass_id, self.plane_id))
        # Passengers arrive two hours before the plane takes off
        arrival_time = int(random.uniform(scheduled_time - 7200, scheduled_time - 900))
        yield self.env.timeout(arrival_time)
        #print("Passenger with id %d and plane id %d arrives at " %(self.pass_id, self.plane_id), env.now)
        # random choose to online checkin of ofline checkin
        a = random.random()
        if a > ONLINE_CHECKIN_RATIO_MEAN:
            self.env.process(pf.on_checkin_process(self))
        else:
            self.env.process(pf.off_checkin_process(self))

class Passenger_Flow(object):
    def __init__(self, env):
        self.env = env
        # generate resources
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
        #yield self.env.timeout(int(random.uniform(TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN - TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD, TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN + TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD)))
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN, TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD)))
        # print("online checkin walk end: ", env.now)
        # time to process
        index = self.shortest_line(self.online_checkin_lines)
        # print("Online checkin started for passeger %d of plane %d at line %d" %(passenger.pass_id, passenger.plane_id, index+1))
        with self.online_checkin_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(ONLINE_CHECKIN_MEAN, ONLINE_CHECKIN_STD)))
            # print("Online checkin completed for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
            passenger.checkin = True
            if airplane_dict[passenger.plane_id].status == False:
                self.env.process(self.immig_process(passenger))
                
    def off_checkin_process(self, passenger):
        # time to walk
        # print("offline checkin walk start: ", env.now)
        #yield self.env.timeout(int(random.uniform(TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN-TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD, TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN+TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD)))
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN, TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD)))
        # print("offline checkin walk end: ", env.now)
        # time to process
        index = self.shortest_line(self.offline_checkin_lines)
        # print("Offline checkin started for passeger %d of plane %d at line %d" %(passenger.pass_id, passenger.plane_id, index+1))
        with self.offline_checkin_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(OFFLINE_CHECKIN_MEAN, OFFLINE_CHECKIN_STD)))
            # print("Offline completed for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
            passenger.checkin = True
            if airplane_dict[passenger.plane_id].status == False:
                self.env.process(self.immig_process(passenger))
    
    def immig_process(self, passenger):
        # time to walk
        # print("Immigration started for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
        # print("immig process walk start: ", env.now)
        #yield self.env.timeout(int(random.uniform(TIME_TO_WALK_TO_IMMIG_MEAN-TIME_TO_WALK_TO_IMMIG_STD, TIME_TO_WALK_TO_IMMIG_MEAN+TIME_TO_WALK_TO_IMMIG_STD)))
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_IMMIG_MEAN, TIME_TO_WALK_TO_IMMIG_STD)))
        # print("immig process walk start: ", env.now)
        # time to process
        index = self.shortest_line(self.immig_lines)
        with self.immig_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(IMMIG_MEAN, IMMIG_STD)))
            # print("Immigration checkin completed for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
            passenger.immig = True
            
            if airplane_dict[passenger.plane_id].status == False:
                self.env.process(self.sec_process(passenger))

    def sec_process(self, passenger):
        # time to walk
        # print("Security check started for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
        # print("security check walk start: ", env.now)
        #yield self.env.timeout(int(random.uniform(TIME_TO_WALK_TO_SEC_MEAN-TIME_TO_WALK_TO_SEC_STD, TIME_TO_WALK_TO_SEC_MEAN+TIME_TO_WALK_TO_SEC_STD)))
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_SEC_MEAN, TIME_TO_WALK_TO_SEC_STD)))
        # print("security check walk end: ", env.now)
        # time to process
        index = self.shortest_line(self.sec_lines)
        with self.sec_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(SEC_MEAN, SEC_STD)))
            # print("Security check completed for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
            passenger.security = True
            
            if airplane_dict[passenger.plane_id].status == False:
                self.env.process(self.board_process(passenger))
            
    def board_process(self, passenger):
        # time to walk
        # print("Boarding started for passeger %d of plane %d" %(passenger.pass_id, passenger.plane_id))
        # print("boarding walk start: ", env.now)
        #yield self.env.timeout(int(random.uniform(TIME_TO_WALK_TO_BOARD_MEAN-TIME_TO_WALK_TO_BOARD_STD, TIME_TO_WALK_TO_BOARD_MEAN+TIME_TO_WALK_TO_BOARD_STD)))
        yield self.env.timeout(abs(random.gauss(TIME_TO_WALK_TO_BOARD_MEAN, TIME_TO_WALK_TO_BOARD_STD)))
        # print("boarding walk end: ", env.now)
        # time to process
        index = self.shortest_line(self.board_lines)
        with self.board_lines[index].request() as request:
            yield request
            yield self.env.timeout(abs(random.gauss(BOARD_MEAN, BOARD_STD)))
            passenger.boarding = True
            if airplane_dict[passenger.plane_id].status == False:
                passenger_dict[passenger.plane_id] = passenger_dict[passenger.plane_id] + 1
                #print("#############Passenger with id %d and plane id %d boarded at " %(passenger.pass_id, passenger.plane_id), env.now)
                #print("airplane passenger number:", passenger_dict, env.now)
class Runnway(object):
    def __init__(self, env, num_runway):
        self.env = env
        self.runway = simpy.Resource(env, num_runway)

    def occupy(self, occupy_time): #function indicating whether runway is occupied or idle
        yield self.env.timeout(occupy_time)

class Airplane(object):
    def __init__(self, env, plane_id, rw, scheduled_time):
        self.env = env
        self.rw = rw
        self.plane_id = plane_id
        self.scheduled_time = scheduled_time
        self.late = False 
        self.flight_cancel = 0 #check if the airplane is late '0 - On Time, 1 - Delay at the airport, 2 - Flight Cancelled'
        self.delay_by = 0 # number of seconds flight is delayed
        self.status = False #Status of Takeoff
        self.actual_take_off_time = 0
        self.actual_land_time = 0
        
    def takeOff(self):

        global delay_index

        if(random_delay_cancel[delay_index] == 1):
            self.delay_by = int(random.uniform(600,900))
            yield self.env.timeout(self.delay_by)
            self.flight_cancel = 1
            print('%s got delayed at the airport due to operations by %.2f ' % (self.plane_id, self.delay_by))
        elif (random_delay_cancel[delay_index] == 2):
            self.flight_cancel = 2
            self.status = False
            print('Flight %s got cancelled ' % (self.plane_id))
            delay_index = delay_index+1
            return

        delay_index = delay_index+1
            
        self.status = True
        with self.rw.runway.request() as request:
            yield request
            self.actual_take_off_time = round(self.env.now, 2) 
            print('%s should take off at %.2f and actually take off at %.2f' % (self.plane_id, self.scheduled_time, self.actual_take_off_time))
            yield self.env.process(self.rw.occupy(TIME_TO_TAKE_OFF))

        
            
    def land(self):
        with self.rw.runway.request() as request:
            yield request
            self.actual_land_time = round(self.env.now, 2) 
            print('%s lands at %.2f' % (self.plane_id, self.actual_land_time))
            yield self.env.process(self.rw.occupy(TIME_TO_LAND))
        
        yield self.env.timeout(TIME_ON_GROUND)

        #self.takeOff()
        #with self.rw.runway.request() as request:
            #yield request
            #yield self.env.process(self.rw.occupy(TIME_TO_TAKE_OFF))


    def schedule(self, time):
        yield self.env.timeout(time)
        # Skip if the plane has already taken off
        if self.status:
            print("Arirplane %s has already taken off" % (self.plane_id))
            pass 
        # Only those with more than 180 boardings are allowed to take off
        if passenger_dict[self.plane_id] >= PASSENGERS_NEED_TO_TAKE_OFF:
            # ready to take off 
            self.env.process(self.takeOff())
        elif self.late and (self.env.now - self.scheduled_time) >= GRACE_PERIOD:
            # If the waiting time exceeds the grace period, the plane takes off directly
            self.env.process(self.takeOff())
        else:
            #After 300 seconds, check if it can take off
            yield self.env.timeout(300)
            self.env.process(self.schedule(300))
            self.late = True
    
    def schedule_land(self, time):
        yield self.env.timeout(time)
        self.env.process(self.land())
class Departure_Table(object):
    def __init__(self, env, runway, pf):
        self.runway = runway
        self.pf = pf
        self.env = env
    
    def schedule(self, num_airplane, scheduled_time):
        for ID in range(1, num_airplane + 1):
            # The first plane took off two hours later, and the rest of the planes took off depend on AIRPLANE_TAKE_OFF_INTERVAL
            if ID == 1:
                #print("plane ID : ",ID)
                airplane = Airplane(self.env, ID, self.runway, scheduled_time)
                passenger_dict[ID] = 0
                airplane_dict[ID] = airplane
                
                PASSENGERS_FOR_CURRENT = random.randint(PASSENGERS_NEED_TO_TAKE_OFF-10,PASSENGERS_PER_AIRPLANES)
                for i in range(1, PASSENGERS_FOR_CURRENT+1):
                    passenger = Passenger(self.env, i, ID)
                    self.env.process(passenger.schedule(scheduled_time, self.pf))
                
                self.env.process(airplane.schedule_land(scheduled_time - TIME_ON_GROUND - TIME_TO_LAND))
                self.env.process(airplane.schedule(scheduled_time))

            if ID != 1:
                #print("plane ID : ",ID)
                passenger_dict[ID] = 0
                airplane = Airplane(self.env, ID, self.runway, scheduled_time + (ID-1) * AIRPLANE_TAKE_OFF_INTERVAL)
                airplane_dict[ID] = airplane
                PASSENGERS_FOR_CURRENT = random.randint(PASSENGERS_NEED_TO_TAKE_OFF-10,PASSENGERS_PER_AIRPLANES)
                for i in range(1, PASSENGERS_FOR_CURRENT+1):
                    passenger = Passenger(self.env, i, ID)
                    self.env.process(passenger.schedule(scheduled_time  + (ID-1) * AIRPLANE_TAKE_OFF_INTERVAL, self.pf))

                self.env.process(airplane.schedule_land(scheduled_time - TIME_ON_GROUND - TIME_TO_LAND + (ID-1) * AIRPLANE_TAKE_OFF_INTERVAL))

                self.env.process(airplane.schedule(scheduled_time + (ID-1) * AIRPLANE_TAKE_OFF_INTERVAL))
# for pygame draw picture
# for pygame draw picture
def draw(env):
    while True:
        # pygame code
        for event in pygame.event.get():
            if event.type == QUIT:
                  exit()

        screen.fill((255,255,255))
       
        # ATF queue line
        pygame.draw.line(screen,(0,0,0),(200, 700),(800,700),3)
        pygame.draw.line(screen,(0,0,0),(200, 740),(800,740),3)


        # rect represent runway 
        #  1 => occupied  0 => idle
        if runway.runway.count == 0:
            pygame.draw.rect(screen, (0,0,0), (880, 670, 100, 100), 3)
        else:
            pygame.draw.rect(screen, (255,0,0), (880, 670, 100, 100))

        # Time
        def time(seconds):
            seconds = round(seconds, 0)
            temp = math.floor(seconds / 60)
            hour = math.floor(temp / 60)
            minute = temp % 60
            second = seconds % 60
            return ("%d:%d:%d" %(hour, minute, second))

        time_now = my_font.render("Time: " + str(time(env.now)), True, (0,0,0), (255, 255, 255))
        screen.blit(time_now, (100, 100))
        # text
        text_head = my_font.render("Airport Simulation", True, (0,0,0), (255, 255, 255))
        screen.blit(text_head, (500, 50))

        text_surface1 = my_font.render("Online checkin lines", True, (0,0,0), (255, 255, 255))
        screen.blit(text_surface1, (280, 175))

        text_surface2 = my_font.render("Offline checkin lines", True, (0,0,0), (255, 255, 255))
        screen.blit(text_surface2, (680, 175))

        text_surface3 = my_font.render("Immig process lines", True, (0,0,0), (255, 255, 255))
        screen.blit(text_surface3, (430, 275))
        
        text_surface4 = my_font.render("Sec process lines", True, (0,0,0), (255, 255, 255))
        screen.blit(text_surface4, (430, 375))

        text_surface5 = my_font.render("Board process lines", True, (0,0,0), (255, 255, 255))
        screen.blit(text_surface5, (430, 475))

        text_surface = my_font.render("ATF queue system", True, (0,0,0), (255, 255, 255))
        screen.blit(text_surface, (430, 675))

        text_surface10 = my_font.render("Runway", True, (0,0,0), (255, 255, 255))
        screen.blit(text_surface10, (880, 635))


        # Online Checkin
        Online_checkin_queue = 0
        Online_congestion = False
        for i in range(len(pf.online_checkin_lines)):
            Online_checkin_queue += len(pf.online_checkin_lines[i].queue)
        
        x_init = 220
        y_init = 220
        Online_queue =  my_font.render("Online queue: " + str(Online_checkin_queue), True, (0,0,0), (255, 255, 255))
        screen.blit(Online_queue, (20, 190))
        # The red line indicates congestion in the queue
        if Online_checkin_queue > 7:
            pygame.draw.line(screen,(255,0,0),(200, 200),(500,200),3)
            pygame.draw.line(screen,(255,0,0),(200, 240),(500,240),3)
            Online_congestion = True
            for i in range(Online_checkin_queue):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40
        else:
            pygame.draw.line(screen,(0,0,0),(200, 200),(500,200),3)
            pygame.draw.line(screen,(0,0,0),(200, 240),(500,240),3)
            for i in range(Online_checkin_queue):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40

        # Offline Checkin
        Offline_checkin_queue = 0
        Offline_congestion = False
        for i in range(len(pf.offline_checkin_lines)):
            Offline_checkin_queue += len(pf.offline_checkin_lines[i].queue)
        
        Offline_queue =  my_font.render("Offline queue: " + str(Offline_checkin_queue), True, (0,0,0), (255, 255, 255))
        screen.blit(Offline_queue, (20, 230))
        
        x_init = 620
        y_init = 220
        if Offline_checkin_queue > 7:
            Offline_congestion = True
            pygame.draw.line(screen,(255,0,0),(600, 200),(900,200),3)
            pygame.draw.line(screen,(255,0,0),(600, 240),(900,240),3)
            for i in range(7):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40
        else:
            pygame.draw.line(screen,(0,0,0),(600, 200),(900,200),3)
            pygame.draw.line(screen,(0,0,0),(600, 240),(900,240),3)
            for i in range(Offline_checkin_queue):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40


        # Immig process lines
        Immig_process_queue = 0
        Immig_congestion = False
        for i in range(len(pf.immig_lines)):
            Immig_process_queue += len(pf.immig_lines[i].queue)
        
        Immig_queue =  my_font.render("Immig queue: " + str(Immig_process_queue), True, (0,0,0), (255, 255, 255))
        screen.blit(Immig_queue, (20, 310))
        
        x_init = 220
        y_init = 320
        if Immig_process_queue > 15:
            Sec_congestion = True
            pygame.draw.line(screen,(255,0,0),(200, 300),(800,300),3)
            pygame.draw.line(screen,(255,0,0),(200, 340),(800,340),3)
            for i in range(15):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40
        else:
            pygame.draw.line(screen,(0,0,0),(200, 300),(800,300),3)
            pygame.draw.line(screen,(0,0,0),(200, 340),(800,340),3)
            for i in range(Immig_process_queue):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40

        # Sec lines  
        Sec_lines_queue = 0
        Sec_congestion = False
        for i in range(len(pf.sec_lines)):
            Sec_lines_queue += len(pf.sec_lines[i].queue)
        
        Sec_queue =  my_font.render("Sec queue: " + str(Sec_lines_queue), True, (0,0,0), (255, 255, 255))
        screen.blit(Sec_queue, (20, 410))

        x_init = 220
        y_init = 420
        if Sec_lines_queue > 15:
            Sec_congestion = True
            pygame.draw.line(screen,(255,0,0),(200, 400),(800,400),3)
            pygame.draw.line(screen,(255,0,0),(200, 440),(800,440),3)
            for i in range(15):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40
        else:
            pygame.draw.line(screen,(0,0,0),(200, 400),(800,400),3)
            pygame.draw.line(screen,(0,0,0),(200, 440),(800,440),3)
            for i in range(Sec_lines_queue):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40

        # Board lines
        Board_lines_queue = 0
        Board_congestion = False
        for i in range(len(pf.board_lines)):
            Board_lines_queue += len(pf.board_lines[i].queue)
        
        Board_queue =  my_font.render("Board queue: " + str(Board_lines_queue), True, (0,0,0), (255, 255, 255))
        screen.blit(Board_queue, (20, 510))
        
        x_init = 220
        y_init = 520
        if Board_lines_queue > 15:
            Board_congestion = True
            pygame.draw.line(screen,(255,0,0),(200, 500),(800,500),3)
            pygame.draw.line(screen,(255,0,0),(200, 540),(800,540),3)
            for i in range(15):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40
        else:
            pygame.draw.line(screen,(0,0,0),(200, 500),(800,500),3)
            pygame.draw.line(screen,(0,0,0),(200, 540),(800,540),3)
            for i in range(Board_lines_queue):
                pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
                x_init = x_init + 40

        # Runway queue
        # draw circle
        # init position x 220 y 620
        Runway_queue =  my_font.render("Runway queue: " + str(len(runway.runway.queue)), True, (0,0,0), (255, 255, 255))
        screen.blit(Runway_queue, (20, 710))
        x_init = 220
        y_init = 720
        for i in range(len(runway.runway.queue)):
            pygame.draw.circle(screen, (0,0,0), (x_init, y_init), 15)
            x_init = x_init + 40

        #Airplane table
        Airplane_table =  my_font.render("Airplane Table", True, (0,0,0), (255, 255, 255))
        screen.blit(Airplane_table, (1020, 110))

        Plane_ID =  my_font.render("ID", True, (0,0,0), (255, 255, 255))
        screen.blit(Plane_ID, (950, 150))
        
        Scheduled_time =  my_font.render("Schedule", True, (0,0,0), (255, 255, 255))
        screen.blit(Scheduled_time, (1020, 150))

        Actual_time =  my_font.render("Actual", True, (0,0,0), (255, 255, 255))
        screen.blit(Actual_time, (1150, 150))

        x_ID = 955
        y_ID = 150
        x_Schedule = 1040
        y_Schedule = 150
        x_Actual = 1150
        y_Actual = 150
        # first render ID and Schedule
        for ID, plane in airplane_dict.items():
            Text_ID =  my_font.render(str(ID), True, (0,0,0), (255, 255, 255))
            screen.blit(Text_ID, (x_ID, y_ID + ID * 30))

            Text_Schedule =  my_font.render(str(time(plane.scheduled_time)), True, (0,0,0), (255, 255, 255))
            screen.blit(Text_Schedule, (x_Schedule, y_Schedule + ID * 30))

            if plane.status:
                Text_Actual =  my_font.render(str(time(plane.actual_take_off_time)), True, (0,0,0), (255, 255, 255))
                screen.blit(Text_Actual, (x_Actual, y_Actual + ID * 30))

        pygame.display.update()

        # simpy code
        # Every 1 time step, check whether the flights that are not on time can take off
        yield env.timeout(1)


def monitor(env, pf, runway):
    while True:
        # Monitor data every minute
        yield env.timeout(60)
        # print("Now: ",env.now)
        time_queue.append(env.now)
        
        print("online checkin lines queue")
        temp = []
        for i in range(len(pf.online_checkin_lines)):
            print(len(pf.online_checkin_lines[i].queue), end=" ")
            temp.append(len(pf.online_checkin_lines[i].queue))
        online_queue.append(temp)
        # print("")

        # print("offline checkin lines queue")
        temp = []
        for i in range(len(pf.offline_checkin_lines)):
            print(len(pf.offline_checkin_lines[i].queue), end=" ")
            temp.append(len(pf.offline_checkin_lines[i].queue))
        offline_queue.append(temp)
        # print("")

        # print("immig lines queue")
        temp = []
        for i in range(len(pf.immig_lines)):
            print(len(pf.immig_lines[i].queue), end=" ")
            temp.append(len(pf.immig_lines[i].queue))
        immig_queue.append(temp)
        # print("")
        
        # print("sec lines queue")
        temp = []
        for i in range(len(pf.sec_lines)):
            print(len(pf.sec_lines[i].queue), end=" ")
            temp.append(len(pf.sec_lines[i].queue))
        sec_queue.append(temp)
        # print("")
        
        # print("board lines queue")
        temp = []
        for i in range(len(pf.board_lines)):
            print(len(pf.board_lines[i].queue), end=" ")
            temp.append(len(pf.board_lines[i].queue))
        board_queue.append(temp)
        # print("")
        
        # print("runway lines queue")
        print(len(runway.runway.queue))
        runway_queue.append(len(runway.runway.queue))
# function to save plots
def individual_plots(queue, time, name):
    plt.figure(figsize=(18,10))
    plt.title(name, {'fontsize': 16})
    plt.plot(time_queue, queue, label = ['queue ' +str(t+1) for t in range(len(queue[0]))])
    # plt.plot(time_queue, queue)
    plt.legend(fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.xlabel("Time Steps", fontsize=16)
    plt.ylabel("No of passengers in each queue", fontsize=16)
    plt.savefig(name, bbox_inches='tight')
    
def combined_plots(queue, time, name):
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["font.size"] = 8
    name_n = name+'_comb'
    new = [sum(item) for item in queue]
    plt.figure(figsize=(3,1.67))
    plt.title(name_n, {'fontsize': 8})
    plt.plot(time_queue, new, label = name_n+' total')
    plt.legend(fontsize=8, frameon=False)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.grid(linestyle='dotted')
    plt.xlabel("Time Steps", fontsize=8)
    plt.ylabel("Total No of passengers in queue", fontsize=8)
    plt.savefig(name_n + ".pdf", bbox_inches='tight')
    return time_queue, new

env = simpy.Environment()
runway = Runnway(env, NUM_RUNWAY) #Creating runway object
pf = Passenger_Flow(env)
departure_Table = Departure_Table(env, runway, pf)
departure_Table.schedule(NO_OF_FLIGHTS_PER_DAY, 7200)
env.process(monitor(env, pf, runway))
env.process(draw(env))
env.run(26000)

#plotting the results
queues = [online_queue, offline_queue, immig_queue, sec_queue, board_queue]
names = ['Online checkin', 'offline checkin', "Immigration", "Security Check", "Boarding"]

for n in range(len(names)):
    # individual_plots(queues[n], time_queue, names[n])
    qt, y_value = combined_plots(queues[n], time_queue, names[n])
    # np.save(str(PTP)+names[n]+str(GRACE_PERIOD)+".npy", [qt, y_value])
    
# printing out the scheduled time and actual time of airplanes
scheduled_time_plane = []
actual_time_plane = []
delay_by_plane = []
for i in range(1, len(airplane_dict) + 1):
    scheduled_time_plane.append(airplane_dict[i].scheduled_time)
    actual_time_plane.append(airplane_dict[i].actual_take_off_time)
    delay_by_plane.append(airplane_dict[i].delay_by)
    print("plane ",i, airplane_dict[i].scheduled_time, airplane_dict[i].actual_take_off_time, airplane_dict[i].status,airplane_dict[i].late, airplane_dict[i].delay_by, airplane_dict[i].flight_cancel )
print("passenger dict", passenger_dict)
np.save(str(GRACE_PERIOD)+"passenger_dict.npy", passenger_dict)
np.save(str(GRACE_PERIOD)+"scheduled.npy", scheduled_time_plane)
np.save(str(GRACE_PERIOD)+"actual.npy", actual_time_plane)
np.save(str(GRACE_PERIOD)+"delay.npy", delay_by_plane)

# saving the parameters to csv file

df = pd.DataFrame(columns=['Parameter_name','Value'])
df.loc[len(df.index)] = ['TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN',TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN]
df.loc[len(df.index)] = ['TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD',TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD]
df.loc[len(df.index)] = ['TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN',TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN] 
df.loc[len(df.index)] = ['TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD',TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD]

df.loc[len(df.index)] = ['TIME_TO_WALK_TO_IMMIG_MEAN',TIME_TO_WALK_TO_IMMIG_MEAN]
df.loc[len(df.index)] = ['TIME_TO_WALK_TO_IMMIG_STD',TIME_TO_WALK_TO_IMMIG_STD]

df.loc[len(df.index)] = ['TIME_TO_WALK_TO_SEC_MEAN',TIME_TO_WALK_TO_SEC_MEAN]
df.loc[len(df.index)] = ['TIME_TO_WALK_TO_SEC_STD',TIME_TO_WALK_TO_SEC_STD]

df.loc[len(df.index)] = ['TIME_TO_WALK_TO_BOARD_MEAN',TIME_TO_WALK_TO_BOARD_MEAN]
df.loc[len(df.index)] = ['TIME_TO_WALK_TO_BOARD_STD',TIME_TO_WALK_TO_BOARD_STD]

df.loc[len(df.index)] = ['ONLINE_CHECKIN_LINES',ONLINE_CHECKIN_LINES]
df.loc[len(df.index)] = ['ONLINE_CHECKIN_CUST_PER_LINE',ONLINE_CHECKIN_CUST_PER_LINE]
df.loc[len(df.index)] = ['ONLINE_CHECKIN_MEAN',ONLINE_CHECKIN_MEAN]
df.loc[len(df.index)] = ['ONLINE_CHECKIN_STD',ONLINE_CHECKIN_STD]

df.loc[len(df.index)] = ['OFFLINE_CHECKIN_LINES',OFFLINE_CHECKIN_LINES]
df.loc[len(df.index)] = ['OFFLINE_CHECKIN_CUST_PER_LINE',OFFLINE_CHECKIN_CUST_PER_LINE]
df.loc[len(df.index)] = ['OFFLINE_CHECKIN_MEAN',OFFLINE_CHECKIN_MEAN]
df.loc[len(df.index)] = ['OFFLINE_CHECKIN_STD',OFFLINE_CHECKIN_STD]

df.loc[len(df.index)] = ['IMMIG_LINES',IMMIG_LINES]
df.loc[len(df.index)] = ['IMMIG_CUST_PER_LINE',IMMIG_CUST_PER_LINE]
df.loc[len(df.index)] = ['IMMIG_MEAN',IMMIG_MEAN]
df.loc[len(df.index)] = ['IMMIG_STD',IMMIG_STD]

df.loc[len(df.index)] = ['SEC_LINES',SEC_LINES]
df.loc[len(df.index)] = ['SEC_CUST_PER_LINE',SEC_CUST_PER_LINE]
df.loc[len(df.index)] = ['SEC_MEAN',SEC_MEAN]
df.loc[len(df.index)] = ['SEC_STD',SEC_STD]

df.loc[len(df.index)] = ['BOARD_LINES',BOARD_LINES]
df.loc[len(df.index)] = ['BOARD_CUST_PER_LINE',BOARD_CUST_PER_LINE]
df.loc[len(df.index)] = ['BOARD_MEAN',BOARD_MEAN]
df.loc[len(df.index)] = ['BOARD_STD',BOARD_STD]

# Parameters - Airplane

df.loc[len(df.index)] = ['TIME_TO_TAKE_OFF',TIME_TO_TAKE_OFF]
df.loc[len(df.index)] = ['TIME_TO_LAND',TIME_TO_LAND]
df.loc[len(df.index)] = ['PASSENGERS_PER_AIRPLANES',PASSENGERS_PER_AIRPLANES]      # plane passenger capacity
df.loc[len(df.index)] = ['PASSENGERS_NEED_TO_TAKE_OFF',PASSENGERS_NEED_TO_TAKE_OFF]  # how many passenger need to take off 
df.loc[len(df.index)] = ['AIRPLANE_TAKE_OFF_INTERVAL',AIRPLANE_TAKE_OFF_INTERVAL]   # planes takes off every hour
df.loc[len(df.index)] = ['GRACE_PERIOD',GRACE_PERIOD]               # the time that the plane waits for late passengers
df.loc[len(df.index)] = ['NUM_RUNWAY',NUM_RUNWAY]                      # number of runway in the airport
df.loc[len(df.index)] = ['TIME_ON_GROUND',TIME_ON_GROUND]               # Arrival aircraft spends 45 minutes at the terminal for de-boarding and boarding (this doesn't include departure schedule)
df.to_csv('Parameters_list.csv')

# saving the parameters and queue lists to csv file
queues = [online_queue, offline_queue, immig_queue, sec_queue, board_queue]
queues.append(time_queue)
names = ['Online checkin', 'offline checkin', "Immigration", "Security Check", "Boarding"]
names.append("Time_stamp")
te = dict()
for n in range(len(names)):
    te[names[n]] = queues[n]
df2 = pd.DataFrame(te)
df2.to_csv("queue_lists.csv")     