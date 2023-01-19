## CSE 6730 Group36 Project 
### Created by Saran Reddy Gopavaram, Mugundhan Murugesan, Xiaoliang Yan, Hui Zhong  

# The Passenger Flow Congestion Effect on Delayed Flight Departure

# 1.Abstract

Modern airports are complex multimodal systems with intertwined relationships among passengers, facilities and airplanes. Significant efforts have been dedicated to optimizing the total flow inside an airport, which can be further broken down into passenger flow and airport traffic. Most prior works have focused on either one of the two systems, namely passenger flow or traffic flow, to reduce the complexity of simulation and uncertainties. While some researchers attempted to integrate simulated airport systems for a holistic evaluation of the airport total flow, prior objectives have been primarily focused on optimizing airport design. However, the relationship between passenger flow and airport traffic should not be simply decoupled when a feedforward relationship is evident. In this project, we aim to answer the following research questions, 1) what are the primary factors contributing to passenger congestion inside an airport terminal, and 2) what is the relationship between passenger congestion and airport flight delay? These questions are answered by simulating the passenger flow, airport traffic flow and the coupling function. As a result, it has been demonstrated that the processing times of airport facilities (e.g., check-in, immigration and security) contribute heavily to the passenger flow in a non-linear fashion, in which case a significant congestion emerges when the processing time crosses a threshold value. The delay caused by this congestion can result in a large number of passengers missing the flight. To this end, the effect of “grace period” in the coupling function has been investigated through simulation as a possible response to significant congestion in passenger flow. We demonstrated that the average delay of flight departure varies linearly with the grace period, while the number of passengers on board the aircraft increases drastically between 20 and 40 minutes of grace period before reaching an asymptote, which suggests that an optimization between the amount of flight delay and the number of passengers on board must be conducted. This finding is validated by the reported airline practice, where on average 12 to 16 minutes of grace period have been reported.       

# 2.Description of the system

**Airport terminal passenger flow system**

The airport passenger flow system is the flow of passengers from entry of the airport to the terminal of the departure aircraft. It can be described using a series of sub-systems comprising check-in desk, Security Check, Immigration, Terminal Gate entry and Boarding. The check-in process is assumed to be of two types: 1) Online: Passengers who completed their check-in online take this queue. 2) Offline: Passengers who are yet to complete their check-in through offline mode take this queue. All other sub-systems are assumed to have a fixed number of queues with time taken at each queue taken as a probability distribution. The number of queues at each sub-system and the values of the probability distributions are decided based on studying the data recorded at existing airports.

**Airport traffic flow system**

The system of interest is an airport with only one runway. The runway of an airport can either be active (being used by another aircraft) or accessible. If the runway is idle when an airplane arrives in the airport&#39;s airspace, the aircraft can use the runway for landing. If the runway is active, the air traffic controller (&quot;ATC&quot; - the simulator in this model) will place the aircraft in a queue until the runway is free to be used. Similarly, ATC will put the plane in a queue when the aircraft is about to takeoff. The system can be determined by three factors: flight schedule, passenger flow and runway. Boarding of passengers impacts when a flight is about to takeoff. Flight schedule impacts the operations of the runway. FIFO order is used to queue the airplanes (for landing and takeoff). ATC will help schedule and maintain the flying list. The events of an aircraft are scheduled based on the runway and the type of weather conditions.

The passenger flow system provides the number of passengers arriving and departing each airport. The simulation computes the circling time (for the aircraft when it enters the airspace), which is the time when an airplane is ready to land but is waiting for its line in the queue. Some input parameters such as the number of aircraft, simulation length in minutes, and airplane passenger capacity are predefined. All the variables are uniformly distributed.

# 3.Conceptual model of the system

**Passenger flow model**

The Airport passenger flow system is formulated using Discrete Event Simulation (DES) model. DES models the operation of a system as a discrete sequence of events in time which starts from a master event followed by sub-events. The master event is taken as the entry of passengers into the airport which triggers the subsequent sub-events. The flowchart below shows the sequence of the passenger flow model:

_1. Check-in:_

We set the initial conditions such that &#39;x&#39; number of passengers enter the airport every &#39;t&#39; timesteps. In &#39;x&#39; passengers a ± b fraction of passengers has completed the Online Check-in process. Those passengers will have less processing time than the passengers who check-in offline. Using this intuition, time steps taken by offline and online check-in process are set as t1 ± z1 and t2 ± z2 respectively.

_2. Immigration:_

We assume that the airport in our system is an international airport and hence an immigration control area is present after the check-in node. The time steps taken at this node is assumed as t3 ± z3.

_3. Gate_

Passengers are queued at the Gate till the time step reaches a certain limit and then are sent for boarding.

_4. Boarding_

Boarding is assumed to take t4 ± z4 time steps and will stop when both the situations described below happens:

- If the ratio of seats filled and total seats reach a certain limit.
- If the time steps cross the departure time of the aircraft and there is a considerable interval between subsequent passengers.

The number of counters or desks in each node will be decided and the passenger flow density will be studied by varying them.

**Airplane traffic flow model**

Airplane traffic flow model will be mainly stimulated by the queueing system. The model will firstly initialize a FIFO queue. When a flight needs to land or take off, the event will be added to the queue. Then, when the runway is idle, the first event of the queue will be taken out and handled. The flowchart below shows the sequence of the airplane traffic flow model:

_1. Flight schedules and landing event_

Initialize the flight schedule and landing event, every t1 time period, there will be a plane ready to land, and every t2 time period, there will be a plane scheduled to take off.

_2. ATC queueing system._

The ATC system will be implemented by a FIFO queue. The queue receives two kinds of events, namely take-off event, and landing event:

- When the plane is hovering in the air and requesting to land, ATC receives the landing request and adds the landing event at the end of the queue.
- When the aircraft requests takeoff after the passenger has completed boarding, ATC will receive the takeoff request and add the takeoff event at the end of the queue.

_3. Runway_

When the runway is idle at time t, the event at the head of the queue will be fetched and processed. Depending on the type of event (takeoff and landing), it will occupy the runway for different durations t3. After the t3 duration, the runway will continue to fetch the next event, repeat until the queue is empty.

# 4.Platform of Development

We are using Python as the programming language to develop the above-mentioned models and visualize the results. Packages such as simpy will be used to facilitate discrete event simulation.

# 5.References

[1]P. F. i Casas, J. Casanovas, and X. Ferran, &quot;Passenger flow simulation in a hub airport: an application to the Barcelona International Airport,&quot; _Simulation Modelling Practice and Theory,_ vol. 44, pp. 78-94, 2014.

[2]S. Takakuwa, T. Oyama, and S. Chick, &quot;Simulation analysis of international-departure passenger flows in an airport terminal,&quot; in _Winter Simulation Conference_, 2003, vol. 2, pp. 1627-1634.

[3]M. R. Gatersleben and S. W. Van der Weij, &quot;Analysis and simulation of passenger flows in an airport terminal,&quot; in _Proceedings of the 31st conference on Winter simulation: Simulation---a bridge to the future-Volume 2_, 1999, pp. 1226-1231.

[4]S. Alodhaibi, R. L. Burdett, and P. K. Yarlagadda, &quot;Framework for airport outbound passenger flow modelling,&quot; _Procedia Engineering,_ vol. 174, pp. 1100-1109, 2017.

[5]G. Tesoriere, T. Campisi, A. Canale, A. Severino, and F. Arena, &quot;Modelling and simulation of passenger flow distribution at terminal of Catania airport,&quot; in _AIP Conference Proceedings_, 2018, vol. 2040, no. 1, p. 140006: AIP Publishing LLC.

[6]Y. Ju, A. Wang, and H. Che, &quot;Simulation and optimization for the airport passenger flow,&quot; in _2007 International Conference on Wireless Communications, Networking and Mobile Computing_, 2007, pp. 6605-6608: IEEE.

[7]G. Guizzi, T. Murino, and E. Romano, &quot;A discrete event simulation to model passenger flow in the airport terminal,&quot; _Mathematical methods and applied computing,_ vol. 2, pp. 427-434, 2009.

[8]S. Qiang, B. Jia, Q. Huang, and R. Jiang, &quot;Simulation of free boarding process using a cellular automaton model for passenger dynamics,&quot; _Nonlinear Dynamics,_ vol. 91, no. 1, pp. 257-268, 2018.

[9]F. Mazur and M. Schreckenberg, &quot;Simulation and optimization of ground traffic on airports using cellular automata,&quot; _Collect. Dyn,_ vol. 3, pp. 1-22, 2018.

[10]G. Andreatta, P. Dell&#39;Olmo, and G. Lulli, &quot;An aggregate stochastic programming model for air traffic flow management,&quot; _European Journal of Operational Research,_ vol. 215, no. 3, pp. 697-704, 2011.

[11]E. Tolstaya, A. Ribeiro, V. Kumar, and A. Kapoor, &quot;Inverse optimal planning for air traffic control,&quot; in _2019 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)_, 2019, pp. 7535-7542: IEEE.

[12]S. Sanjeevi and S. Venkatachalam, &quot;Robust flight schedules with stochastic programming,&quot; _Annals of Operations Research,_ vol. 305, no. 1, pp. 403-421, 2021.

# 6. Simulation Demo 

![Simulation Demo](https://github.gatech.edu/storage/user/59778/files/e6652899-ba66-43a3-858f-d6f8580f05be)


# 7.Project Git Repository

https://github.gatech.edu/xyan72/CSE6730_Group36.git

# 8. Link to the Project video  
https://mediaspace.gatech.edu/media/%5BTeam+36%5D+The+passenger+flow+congestion+effect+on+delayed+flight+departure/1_0r4pdj4y  

# 9. How to run the simulation

-- Edit parameters as required on Final/Group36FinalModel.py  
-- Run Final/Group36FinalModel.py  
-- Use the created plots and .csv files for the analysis  
  
--- The final report can be found in the "Final" folder.

