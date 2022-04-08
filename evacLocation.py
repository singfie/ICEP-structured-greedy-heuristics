"""
@fiete
November 12, 2020
"""

# import packages
import pandas as pd

# import dependent classes
from location import Location

class EvacLocation(Location):
    """
    A class defining an evacuation location that is used as a gathering point for evacuees.
    This class inherits data from the location class.
    This is a type of node in the network.
    """
    
    def __init__(self, loc_data, scenario_data, scenario_name):
        """
        Initializes an evacuation location and its data.
        """
        Location.__init__(self, loc_data)
        self.total_evacuees = scenario_data['Demand'][(scenario_data['Location'] == self.name) & 
                                                (scenario_data['Scenario'] == scenario_name)].values
        self.private_evacuees = scenario_data['private_evac'][(scenario_data['Location'] == self.name) & 
                                                (scenario_data['Scenario'] == scenario_name)].values
        self.current_evacuees = self.total_evacuees - self.private_evacuees