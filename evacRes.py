"""
@fiete
November 12, 2020
"""

# import packages
import pandas as pd


class EvacRes():
    """
    A class that defines the evacuation resource and holds its performance parameters.
    This class can represent a vessel, an aircraft or other evacuation resources
    """
    
    def __init__(self, res_data, initial_docks):
        """
        Initializes an evacuation resource and requires data about the resource.
        This can be handed over in a separated row of a .csv input.
        """
        
        # performance parameters
        
        self.name = res_data.loc['Vessel_name']# resource name
        self.type = res_data.loc['Vessel_type'] # resource type
        self.contract_cost = res_data.loc['contract_cost'] # contract cost to select the resource into the fleet
        self.operating_cost = res_data.loc['operating_cost'] # operating cost per hour of this resource
        self.regular_origin = next((x for x in initial_docks if x.name == res_data.loc['Regular_origin']), None) # regular origin of this resource
        self.max_cap = res_data.loc['max_cap'] # maximum passenger capacity of the resource
        self.vmax = res_data.loc['vmax'] # maximum speed of empty resource
        self.vloaded = res_data.loc['v_loaded'] # maximum speed of loaded resource
        self.loading_time = res_data.loc['loading time'] # loading time of the resource
        self.time_to_availability = res_data.loc['time to availability'] # time to availability of the resource
        
        # modeling properties
        
        self.route = [] # list that represents the route segments the resource will take
        self.route.append(self.regular_origin)
        self.passengers_route = [] # list that records the passenger loads on every route leg
        self.current_route_time = self.time_to_availability # current cost of the route in terms of time, initialized as time to availability
        self.current_number_movements = 0 # current number of movements
        self.current_dock = self.regular_origin
        
    def recover_previous_parameters(self, d):
        
        # a function to initialize the route from a passed dictionary 
        self.__dict__ = d
        
    def update_route_time(self, island_docks, mainland_docks):
        
        # a function to update the current route time
        route_time = self.time_to_availability
        for i in range(len(self.route) - 1):
            if self.route[i+1].name in [x.name for x in island_docks]:
                route_time = route_time + (self.loading_time + (self.route[i].distances['Distance'][self.route[i].distances['Destination'] == self.route[i+1].name]/self.vmax) * 60).values[0]
            elif self.route[i+1].name in [x.name for x in mainland_docks]:
                route_time = route_time + (self.loading_time + (self.route[i].distances['Distance'][self.route[i].distances['Destination'] == self.route[i+1].name]/self.vloaded) * 60).values[0]
        self.current_route_time = route_time
        self.current_number_movements = len(self.route) - 1
        self.current_dock = self.route[-1]

