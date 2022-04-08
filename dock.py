"""
@fiete
November 12, 2020
"""

# import packages
import pandas as pd

class Dock:
    """
    A class defining a dock that is located at a location. 
    This dock can be used by evacuation resources to land and load or unload evacuees.
    This is a type of node in the network.
    """
    
    def __init__(self, dock_data, distance_data, compat_data):
        """
        Initializes the dock and its data. 
        The compatibility determines whether this dock can be used by a specific resource.
        """
        
        # fixed parameters
        self.name = dock_data.loc['Dock'] # one name
        self.location = dock_data.loc['Location'] # can only take a single value
        self.type = dock_data.loc['Type']
        
        self.compatibility = [i for i in compat_data['Resource'][(compat_data['Dock'] == self.name) & 
                                                     (compat_data['Compatibility'] == 1)]]
        
        self.distances = distance_data[['Destination', 'Distance']][distance_data['Origin'] == self.name].reset_index(drop=True) # [['Destination', 'Distance']]