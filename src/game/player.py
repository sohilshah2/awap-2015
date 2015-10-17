import networkx as nx
import random
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

        graph = state.get_graph()
        paths = nx.all_pairs_shortest_path_length(graph)

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
        self.stations = [best]

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
        station = self.first_station

        commands = []
        if not self.has_built_station:
            commands.append(self.build_command(self.first_station))
            self.has_built_station = True
            self.number_of_stations = 1
            self.current_build_cost *= BUILD_FACTOR

        #cutoff = 
        #if self.number_of_stations < cutoff



        pending_orders = state.get_pending_orders()

        for (order, path) in state.get_active_orders():
            for i in range(len(path)-1):
                graph.remove_edge(path[i], path[i+1])

        best_money = 0
        best_order = None
        best_path = None
        for station in self.stations:   
            for order in pending_orders:
                try:
                    path = nx.shortest_path(graph, station, order.get_node())
                    value = order.get_money() - DECAY_FACTOR*len(path)
                except nx.NetworkXNoPath:
                    path = None
                    value = 0
                if value > best_money:
                    best_money = value
                    best_order = order
                    best_path = path
            if best_path != None:
                commands.append(self.send_command(order, path))


        # if len(pending_orders) != 0:
        #     order = random.choice(pending_orders)
        #     path = nx.shortest_path(graph, station, order.get_node())
        #     if self.path_is_valid(state, path):
        #         commands.append(self.send_command(order, path))

        return commands
