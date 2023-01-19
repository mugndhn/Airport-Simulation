from cProfile import run
import numpy as np
import pandas as pd
import random
import simpy
import math

import pygame
from pygame.locals import *

# Parameters - Passengers
ONLINE_CHECKIN_RATIO_MEAN = 0.6   #Control the proportion of passengers using online and offline checkin

TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN = 5
TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD = 2.5
TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN = 5
TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD = 2.5

TIME_TO_WALK_TO_IMMIG_MEAN = 5
TIME_TO_WALK_TO_IMMIG_STD = 1

TIME_TO_WALK_TO_SEC_MEAN = 5
TIME_TO_WALK_TO_SEC_STD = 1

TIME_TO_WALK_TO_BOARD_MEAN = 5
TIME_TO_WALK_TO_BOARD_STD = 1

ONLINE_CHECKIN_LINES = 5
ONLINE_CHECKIN_CUST_PER_LINE = 1
ONLINE_CHECKIN_MEAN = 60
ONLINE_CHECKIN_STD = 2

OFFLINE_CHECKIN_LINES = 5
OFFLINE_CHECKIN_CUST_PER_LINE = 1
OFFLINE_CHECKIN_MEAN = 60
OFFLINE_CHECKIN_STD = 2

IMMIG_LINES = 2
IMMIG_CUST_PER_LINE = 1
IMMIG_MEAN = 60
IMMIG_STD = 5

SEC_LINES = 3
SEC_CUST_PER_LINE = 1
SEC_MEAN = 60
SEC_STD = 5

BOARD_LINES = 1
BOARD_CUST_PER_LINE = 1
BOARD_MEAN = 60
BOARD_STD = 4

# Parameters - Airplane

TIME_TO_TAKE_OFF = 600
TIME_TO_LAND = 600
PASSENGERS_PER_AIRPLANES = 200      # plane passenger capacity
PASSENGERS_NEED_TO_TAKE_OFF = 180   # how many passenger need to take off 
AIRPLANE_TAKE_OFF_INTERVAL = 3600   # planes takes off every hour
GRACE_PERIOD = 1000000                # the time that the plane waits for late passengers
NUM_RUNWAY = 1                      # number of runway in the airport
TIME_ON_GROUND = 2700               # Arrival aircraft spends 45 minutes at the terminal for de-boarding and boarding (this doesn't include departure schedule)

# Global Dictionary
passenger_dict = dict()
airplane_dict = dict()

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
        # print("Passenger with id %d and plane id %d scheduled" %(self.pass_id, self.plane_id))
        # Passengers arrive two hours before the plane takes off
        arrival_time = int(random.uniform(scheduled_time - 7200, scheduled_time))
        yield self.env.timeout(arrival_time)
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
        # print("airplane passenger number:", passenger_dict, env.now)

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
        self.late = False #check if the airplane is late (default is False)
        self.status = False #Status of Takeoff
        self.actual_take_off_time = 0
        self.actual_land_time = 0
        
    def takeOff(self):
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
            print('%s should land at %.2f and actually land at %.2f' % (self.plane_id, self.scheduled_time, self.actual_land_time))
            yield self.env.process(self.rw.occupy(TIME_TO_LAND))
        
        yield self.env.timeout(TIME_ON_GROUND)
        with self.rw.runway.request() as request:
            yield request
            yield self.env.process(self.rw.occupy(TIME_TO_TAKE_OFF))


    def schedule(self, time):
        yield self.env.timeout(time)
        # Skip if the plane has already taken off
        if self.status:
            pass 
        # Only those with more than 180 boardings are allowed to take off
        if passenger_dict[self.plane_id] >= PASSENGERS_NEED_TO_TAKE_OFF:
            # ready to take off 
            self.env.process(self.takeOff())
        elif self.late and (self.env.now - self.scheduled_time) >= GRACE_PERIOD:
            # If the waiting time exceeds the grace period, the plane takes off directly
            self.env.process(self.takeOff())
        else:
            # After 300 seconds, check if it can take off
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
                print("plane ID : ",ID)
                airplane = Airplane(self.env, ID, self.runway, scheduled_time)
                passenger_dict[ID] = 0
                airplane_dict[ID] = airplane
                self.env.process(airplane.schedule(scheduled_time))
                for i in range(0, PASSENGERS_PER_AIRPLANES):
                    passenger = Passenger(self.env, i, ID)
                    self.env.process(passenger.schedule(scheduled_time, self.pf))
            if ID != 1:
                print("plane ID : ",ID)
                passenger_dict[ID] = 0
                airplane = Airplane(self.env, ID, self.runway, scheduled_time + (ID - 1) * AIRPLANE_TAKE_OFF_INTERVAL)
                airplane_dict[ID] = airplane
                self.env.process(airplane.schedule(scheduled_time + (ID - 1) * AIRPLANE_TAKE_OFF_INTERVAL))
                for i in range(0, PASSENGERS_PER_AIRPLANES):
                    passenger = Passenger(self.env, i, ID)
                    self.env.process(passenger.schedule(scheduled_time  + (ID - 1) * AIRPLANE_TAKE_OFF_INTERVAL, self.pf))          

# Schedule the flight land time
class Land_Table(object):
    def __init__(self, env, runway):
        self.runway = runway
        self.env = env
    def schedule(self, num_airplane, scheduled_time):   
        for i in range(1, num_airplane + 1):
            airplane = Airplane(self.env, 'Land_airplane %d' % i, self.runway, scheduled_time * i)
            self.env.process(airplane.schedule_land(scheduled_time * i))


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
        print("Now: ",env.now)
        
        print("online checkin lines queue")
        for i in range(len(pf.online_checkin_lines)):
            print(len(pf.online_checkin_lines[i].queue), end=" ")
        print("")
        
        print("offline checkin lines queue")
        for i in range(len(pf.offline_checkin_lines)):
            print(len(pf.offline_checkin_lines[i].queue), end=" ")
        print("")

        print("immig lines queue")
        for i in range(len(pf.immig_lines)):
            print(len(pf.immig_lines[i].queue), end=" ")
        print("")
        
        print("sec lines queue")
        for i in range(len(pf.sec_lines)):
            print(len(pf.sec_lines[i].queue), end=" ")
        print("")
        
        print("board lines queue")
        for i in range(len(pf.board_lines)):
            print(len(pf.board_lines[i].queue), end=" ")
        print("")
        
        print("runway lines queue")
        print(len(runway.runway.queue))


env = simpy.Environment()
runway = Runnway(env, NUM_RUNWAY) #Creating runway object
pf = Passenger_Flow(env)
departure_Table = Departure_Table(env, runway, pf)
departure_Table.schedule(5, 7200)
land_Table = Land_Table(env, runway)
land_Table.schedule(5, 3000)
# env.process(monitor(env, pf, runway))
env.process(draw(env))
env.run(100000)

for i in range(1, len(airplane_dict) + 1):
    print("plane ",i, airplane_dict[i].scheduled_time, airplane_dict[i].actual_take_off_time, airplane_dict[i].status)
    
print("passenger dict", passenger_dict)