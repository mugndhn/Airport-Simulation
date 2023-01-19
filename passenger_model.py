import numpy as np
import pandas as pd
import random
import simpy

RANDOM_SEED = 42
PAS_ARRIVAL_MEAN = 5
PAS_NUMBER_MEAN = 500
PAS_NUMBER_STD = 50
num_airplane = 5
time_interval = 5

# schedule passenger arrival
class Passenger_Arrival(object):
    def __init__(self, env, num_airplane, time_interval, PAS_NUMBER_MEAN, PAS_NUMBER_STD):
        self.num_airplane = num_airplane
        self.time_interval = time_interval
        self.passengers = []

    def schedule(self):
        for i in range(self.num_airplane):
            random.seed(42)
            pass_num = random.gauss(PAS_NUMBER_MEAN,PAS_NUMBER_STD)
            print("Passengers Arrived")
            passenger = Passenger(env, pass_num)
            self.passengers.append(passenger)
            env.process(passenger.arrival(i*self.time_interval, time_interval))

# defining the simulation
class Passenger(object):
    def __init__(self, env, pass_num):
        self.env = env
        self.pass_num = pass_num
        self.ONLINE_CHECKIN_RATIO_MEAN = 0.6
        self.GROUP_SIZE_MEAN = 2.25
        self.GROUP_SIZE_STD = 0.50

        self.TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN = 1
        self.TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD = 0.25
        self.TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN = 1
        self.TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD = 0.25

        self.TIME_TO_WALK_TO_IMMIG_MEAN = 0.5
        self.TIME_TO_WALK_TO_IMMIG_STD = 0.1

        self.TIME_TO_WALK_TO_SEC_MEAN = 0.5
        self.TIME_TO_WALK_TO_SEC_STD = 0.1

        self.ONLINE_CHECKIN_LINES = 5
        self.ONLINE_CHECKIN_CUST_PER_LINE = 1
        self.ONLINE_CHECKIN_MEAN = 2
        self.ONLINE_CHECKIN_STD = 0.2

        self.OFFLINE_CHECKIN_LINES = 5
        self.OFFLINE_CHECKIN_CUST_PER_LINE = 1
        self.OFFLINE_CHECKIN_MEAN = 2
        self.OFFLINE_CHECKIN_STD = 0.2

        self.IMMIG_LINES = 5
        self.IMMIG_CUST_PER_LINE = 1
        self.IMMIG_MEAN = 5
        self.IMMIG_STD = 0.5

        self.SEC_LINES = 10
        self.SEC_CUST_PER_LINE = 1
        self.SEC_MEAN = 5
        self.SEC_STD = 0.5
        print("Passengers Created")
        
    def arrival(self, time, next_pass_arr):
        yield env.timeout(time)
        self.online_checkin_lines = [simpy.Resource(env, capacity = self.ONLINE_CHECKIN_CUST_PER_LINE) for _ in range(self.ONLINE_CHECKIN_LINES)]
        self.offline_checkin_lines = [simpy.Resource(env, capacity = self.OFFLINE_CHECKIN_CUST_PER_LINE) for _ in range(self.OFFLINE_CHECKIN_LINES)]
        self.immig_lines = [simpy.Resource(env, capacity = self.IMMIG_CUST_PER_LINE) for _ in range(self.IMMIG_LINES)]
        self.sec_lines = [simpy.Resource(env, capacity = self.SEC_CUST_PER_LINE) for _ in range(self.SEC_LINES)]
        print("Lines Generated")
        #storing unique ids for visualization purpose
        next_pass_arr_id = 0
        next_pass_id = 0
        while True:
            next_pass_arr = ARRIVALS.pop()
            on_board = self.pass_number

            # wait for the pass arrival
            yield env.timeout(next_pass_arr)

            # updating passenger id and number of pass in queue after each arrival cycle
            pass_ids = list(range(next_pass_id, next_pass_id + on_board))
            next_pass_id += on_board
            next_pass_arr_id += 1

            while len(pass_ids) > 0:
                remaining = len(pass_ids)
                group_size = min(round(random.gauss(self.GROUP_SIZE_MEAN,self.GROUP_SIZE_STD)), remaining)
                pass_processed = pass_ids[-group_size:] # Grab the last `group_size` elements
                pass_ids = pass_ids[:-group_size] # reset pass_ids to only those remaining

                # Randomly determine if the group is going to offline or online check-in           
                if random.random() > self.ONLINE_CHECKIN_RATIO_MEAN:
                    env.process(self.online_checkin_passenger(env, pass_processed))
                    print("Online checkin started")
                else:
                    env.process(offline_checkin_passenger(env, pass_processed, self.offline_checkin_lines))
                    print("Offline checkin started")


    def online_checkin_passenger(self, env, pass_processed, online_checkin_lines):
        #walk to the counter
        walk_begin = env.now
        yield env.timeout(random.gauss(self.TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_MEAN, self.TIME_TO_WALK_TO_ONLINE_CHECKIN_COUNTER_STD))
        walk_end = env.now

        #Assuming the passenger will always pick the shortest line
        online_checkin_line = self.pick_shortest(online_checkin_lines)
        with online_checkin_line[0].request() as req:
            for passe in pass_processed:
                checkin_begin = env.now
                yield env.timeout(random.gauss(self.ONLINE_CHECKIN_MEAN, self.ONLINE_CHECKIN_STD)) # checkin process
                checkin_end = env.now
                env.process(immig_passenger(env, pass_processed, self.immig_lines))

    def offline_checkin_passenger(self, env, pass_processed, offline_checkin_lines):
        #walk to the counter
        walk_begin = env.now
        yield env.timeout(random.gauss(self.TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_MEAN, self.TIME_TO_WALK_TO_OFFLINE_CHECKIN_COUNTER_STD))
        walk_end = env.now

        #Assuming the passenger will always pick the shortest line
        offline_checkin_line = self.pick_shortest(offline_checkin_lines)
        with offline_checkin_line[0].request() as req:
            for passe in pass_processed:
                checkin_begin = env.now
                yield env.timeout(random.gauss(self.OFFLINE_CHECKIN_MEAN, self.OFFLINE_CHECKIN_STD)) # checkin process
                checkin_end = env.now
                env.process(immig_passenger(env, pass_processed, self.immig_lines))

    def immig_passenger(self, env, pass_processed,immig_lines):
        walk_begin = env.now
        yield env.timeout(random.gauss(self.TIME_TO_WALK_TO_IMMIG_MEAN, self.TIME_TO_WALK_TO_IMMIG_STD))
        walk_end = env.now

        # Assuming the passenger will always pick the shortest line
        immig_line = pick_shortest(immig_lines)
        with immig_line[0].request() as req:
            for passe in pass_processed:
                immig_begin = env.now
                yield env.timeout(random.gauss(self.IMMIG_MEAN, self.IMMIG_STD)) # immigration process
                immig_end = env.now
                env.process(security_passenger(env, pass_processed, self.sec_lines))

    def security_passenger(self, env, pass_processed, sec_lines):
        walk_begin = env.now
        yield env.timeout(random.gauss(self.TIME_TO_WALK_TO_SEC_MEAN, self.TIME_TO_WALK_TO_SEC_MEAN))
        walk_end = env.now

        # Assuming the passenger will always pick the shortest line
        sec_line = self.pick_shortest(sec_lines)
        with sec_line[0].request() as req:
            for passe in pass_processed:
                sec_begin = env.now
                yield env.timeout(random.gauss(self.SEC_MEAN, self.SEC_STD)) # security process
                sec_end = env.now

def sim(env):
    passenger_arr_table = Passenger_Arrival(env, num_airplane, time_interval, PAS_NUMBER_MEAN, PAS_NUMBER_STD)
    env.process(passenger_arr_table.schedule())
    
# Setup and Start the simulation
print("Passenger Arrival")
random.seed(RANDOM_SEED)

# Create an environment and start the setup process
env = simpy.Environment()
env.process(sim(env))

# Execute!
env.run(1000)