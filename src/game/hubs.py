from settings import *
import networkx as nx
from collections import Counter
import math

class HubEstimator(object):

    def __init__(self, graph):
        self.graph = graph
        self.nodes = graph.nodes()
        self.total_distances = {v:0 for v in self.nodes}
        return

    def add_order_location(self, order_loc):
        dists = nx.single_source_shortest_path_length(self.graph, order_loc)
        self.total_distances = {v: self.total_distances[v] + math.exp(1.0-dists[v]) for v in self.nodes}
        
    def get_local_maxes(self):
        vtxs = []
        for vtx in self.nodes:
            nbrs = self.graph.neighbors(vtx)
            my_d = self.total_distances[vtx]
            is_local_max = True
            for v in nbrs:
                if self.total_distances[v] > my_d:
                    is_local_max = False
            if is_local_max:
                vtxs.append((vtx, my_d))
        return sorted(vtxs, key=lambda (x,y): y, reverse=True)
        
    
