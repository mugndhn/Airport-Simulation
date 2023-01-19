import numpy
import simpy

class Gate (object):
    def __init__(self, env, planeCapacity=200, boardRate=10, Threshold=3, DepartSchedule=30):
        self.env = env
        self.plane_capacity = planeCapacity
        self.board_rate = boardRate
        self.wait_threshold = Threshold
        self.plane_depart_schedule = DepartSchedule
        self.queue = 0
        self.is_boarding = False
        self.plane_wait_status = 0
        self.plane_on_land = 0
        
    def queue_update(self, add_to_queue):
        """
            Update the terminal gate queue based on boarding conditions
            Add to queue according to number of people passing immigration to the gate
            Remove people from queue when plane is here and passenger starts boarding
            Check how long the plane has waited for passenger, if longer than threshold,
            plane will no longer accept new passengers.

        Args:
        -   add_to_queue: number of people from checkin, immigration and standby
        Returns:
        -   queue: number of people at queue (still in airport/congestion)
        """
        self.queue += add_to_queue
        if self.is_boarding:
            self.plane_on_land += 1
            if self.queue > self.boardRate:
                self.queue -= self.board_rate
            elif self.queue == 0:
                self.plane_wait_status += 1
                if self.plane_wait_status > self.wait_threshold and self.plane_on_land > self.plane_depart_schedule:
                    self.plane_departs()
            else:
                self.queue = 0
        return self.queue

    def plane_arrives(self):
        """
            Update the plane status
        Args:
        -   none
        Returns:
        -   none
        """
        self.is_boarding = True
        
    def plane_departs(self):
        """
            Update the plane status for departure
            Assume a fixed time of planned departure from arrival time
            when called reset initial states and change flight status
        Args:
        -   none
        Returns:
        -   none
        """
        self.is_boarding = False
        self.plane_on_land = 0
        self.plane_wait_status = 0


