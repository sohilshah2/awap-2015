import networkx as nx
import random
import math
from base_player import BasePlayer
from settings import *

class Player(BasePlayer):
    """
    You will implement this class for the competition. DO NOT change the class
    name or the base class.
    """

    # You can set up static state here
    has_built_station = False

    def __init__(self, state):
        """
        Initializes your Player. You can set up persistent state, do analysis
        on the input graph, engage in whatever pre-computation you need. This
        function must take less than Settings.INIT_TIMEOUT seconds.
        --- Parameters ---
        state : State
            The initial state of the game. See state.py for more information.
        """
        self.hubEst = HubEstimator(state.get_graph()) 

        graph = state.get_graph()
        paths = nx.all_pairs_shortest_path_length(graph)

        total = sum([sum([paths[source][target] for target in paths[source]]) \
                      for source in paths])
        avg_pairwise_dist = total / (GRAPH_SIZE*(GRAPH_SIZE-1)/2.0)
        self.threshold = SCORE_MEAN - DECAY_FACTOR*avg_pairwise_dist
        print self.threshold

        shortest = -1
        best = None
        for source in paths.keys():
            length = sum([paths[source][target] for target in paths[source]])
            if shortest < 0:
                shortest = length
                best = source
            elif length < shortest:
                shortest = length
                best = source

        self.first_station = best
        self.number_of_stations = 0
        self.current_build_cost = INIT_BUILD_COST
        #self.stations = [best]
        self.stations = []
        self.number_of_orders = 0

        return

    # Checks if we can use a given path
    def path_is_valid(self, state, path):
        graph = state.get_graph()
        for i in range(0, len(path) - 1):
            if graph.edge[path[i]][path[i + 1]]['in_use']:
                return False
        return True

    def step(self, state):
        """
        Determine actions based on the current state of the city. Called every
        time step. This function must take less than Settings.STEP_TIMEOUT
        seconds.
        --- Parameters ---
        state : State
            The state of the game. See state.py for more information.
        --- Returns ---
        commands : dict list
            Each command should be generated via self.send_command or
            self.build_command. The commands are evaluated in order.
        """

        # We have implemented a naive bot for you that builds a single station
        # and tries to find the shortest path from it to first pending order.
        # We recommend making it a bit smarter ;-)

        graph = state.get_graph()
        #station = graph.nodes()[len(graph.nodes()/2)]
        #station = self.first_station
        time = state.get_time()

        commands = []
        if not self.has_built_station:
            commands.append(self.build_command(self.first_station))
            self.has_built_station = True
            self.number_of_stations = 1
            self.current_build_cost *= BUILD_FACTOR
            self.stations.append(self.first_station)

        #cutoff = 
        #if self.number_of_stations < cutoff



        pending_orders = state.get_pending_orders()
        new_orders = [order for order in pending_orders if order.time_created == time]
        self.number_of_orders += len(new_orders)
        #if self.number_of_orders < ORDER_VAR*HUBS:
        for order in new_orders:
            self.hubEst.add_order_location(order.node)
        self.ms = self.hubEst.get_local_maxes()
        #print len(ms)
        #print ms

        time_left = 1000-time

        money = state.get_money()

        if time % 50 == 0:
            print "money:", state.get_money()
            print "stations:", self.number_of_stations
            print "hubs:", len(self.ms)

        # if (self.number_of_orders > HUBS*2 - ORDER_VAR):
        #     if self.number_of_stations == 0:
        #         commands.append(self.build_command(ms[0][0]))
        #         self.has_built_station = True
        #         self.number_of_stations += 1
        #         self.current_build_cost *= BUILD_FACTOR
        #         self.stations.append(ms[0][0])


        if (self.number_of_orders > HUBS*3+10):
            for (hub,val) in self.ms:
                total_dist = sum([nx.shortest_path_length(graph, hub, station)\
                                 for station in self.stations])
                if self.number_of_stations == 0:
                    commands.append(self.build_command(hub))
                    self.has_built_station = True
                    self.number_of_stations += 1
                    self.current_build_cost *= BUILD_FACTOR
                    self.stations.append(hub)
                first = time_left*ORDER_CHANCE*math.log(val)\
                        /float(self.number_of_orders+1)
                second = total_dist/(float(self.number_of_stations+1)*ORDER_VAR)
                if SCORE_MEAN*math.sqrt(HUBS)*(first + second) > self.current_build_cost \
                    and self.current_build_cost < money and \
                    hub not in self.stations:
                    commands.append(self.build_command(hub))
                    self.number_of_stations += 1
                    money -= self.current_build_cost
                    self.current_build_cost *= BUILD_FACTOR
                    self.stations.append(hub)



        for (order, path) in state.get_active_orders():
            for i in range(len(path)-1):
                graph.remove_edge(path[i], path[i+1])

        possible_orders = []
        threshold = SCORE_MEAN / 20

        for station in self.stations:   
            for order in pending_orders:
                try:
                    path = nx.shortest_path(graph, station, order.get_node())
                    value = order.get_money() - DECAY_FACTOR*len(path) - \
                            DECAY_FACTOR*(time - order.time_created)
                except nx.NetworkXNoPath:
                    path = None
                    value = 0
                if value > threshold:
                    possible_orders.append((order, value, path))

        seen = []
        for (order, value, path) in sorted(possible_orders,
                                           key=lambda(x,y,z):y, reverse=True):
            if value < threshold: break
            if order in seen: continue
            indicator = True
            for i in range(len(path)-1):
                if graph.has_node(path[i]) and graph.has_node(path[i+1]):
                    if not graph.has_edge(path[i], path[i+1]):
                        indicator = False
            if indicator:
                assert(value > threshold)
                commands.append(self.send_command(order, path))
                seen.append(order)
                for i in range(len(path)-1):
                    graph.remove_edge(path[i], path[i+1])




        # if len(pending_orders) != 0:
        #     order = random.choice(pending_orders)
        #     path = nx.shortest_path(graph, station, order.get_node())
        #     if self.path_is_valid(state, path):
        #         commands.append(self.send_command(order, path))

        return commands

class HubEstimator(object):

    def __init__(self, graph):
        self.graph = graph
        self.nodes = graph.nodes()
        self.total_distances = {v:0 for v in self.nodes}
        return

    def add_order_location(self, order_loc):
        dists = nx.single_source_shortest_path_length(self.graph, order_loc)
        self.total_distances = {v: self.total_distances[v] + math.exp(-ORDER_VAR * dists[v]) for v in self.nodes}
        
    def get_local_maxes(self):
        # Could smoooth with ORDER_VAR
        #smoothed = {vtx: 0 for vtx in self.nodes}
        #for v in self.nodes:
        #    nbrs = self.graph.neighbors(v)
        #    nbr_maxes = map(lambda x: self.total_distances[x], nbrs)
        #    smoothed[v] = sum(nbr_maxes) / len(nbrs)
        smoothed = self.total_distances

        vtxs = []
        for vtx in self.nodes:
            nbrs = self.graph.neighbors(vtx)
            my_d = smoothed[vtx]
            is_local_max = True
            for v in nbrs:
                if smoothed[v] > my_d:
                    is_local_max = False
            if is_local_max:
                vtxs.append((vtx, my_d))
        return sorted(vtxs, key=lambda (x,y): y, reverse=True)[0:min(HUBS+5,len(vtxs))]
        
