"""
@fiete
November 12, 2020
"""

# import packages
import pandas as pd

def generate_results_table(resources):
    """
    A function to generate printable results of a route plan that can be saved in .csv format
    """
    
    # create an empty template
    route_details = pd.DataFrame({
                   'segment_id': pd.Series([], dtype='int'),
                   'resource_id': pd.Series([], dtype='str'),
                   'route_segment_id': pd.Series([], dtype='int'),
                   'origin': pd.Series([], dtype='str'),
                   'destination': pd.Series([], dtype='str'),
                   'route_start_time': pd.Series([], dtype='float'),
                   'route_end_time': pd.Series([], dtype='float'),
                   'load_start_time': pd.Series([], dtype='float'),
                   'load_end_time': pd.Series([], dtype='float'),
                   'resource_speed': pd.Series([], dtype='float'),
                   'evacuees': pd.Series([], dtype='int')
    })
    
    # sort the resources list
    resources.sort(key=lambda x: x.name, reverse=False)
    
    # assign the data to each entry
    for i in resources:
        route_segment_id = 1
        for j in range(1,len(i.route)):
            if j == 1:
                route_start_time = i.time_to_availability
            else:
                route_start_time = route_details['load_end_time'].iloc[-1]
            if i.passengers_route[j-1] > 0:
                vessel_speed = i.vloaded
            else:
                vessel_speed = i.vmax
            route_details = route_details.append({'segment_id' : len(route_details), 
                                          'resource_id' : i.name, 
                                          'route_segment_id' : route_segment_id,
                                          'origin': i.route[j-1].name, 
                                          'destination': i.route[j].name,
                                          'route_start_time': route_start_time,
                                          'route_end_time': route_start_time + 
                                                  ((i.route[j-1].distances['Distance'][i.route[j-1].distances['Destination'] == i.route[j].name]/vessel_speed) * 60).values[0],
                                          'load_start_time': route_start_time + 
                                                  ((i.route[j-1].distances['Distance'][i.route[j-1].distances['Destination'] == i.route[j].name]/vessel_speed) * 60).values[0],
                                          'load_end_time': route_start_time + 
                                                  ((i.route[j-1].distances['Distance'][i.route[j-1].distances['Destination'] == i.route[j].name]/vessel_speed) * 60).values[0] + 
                                                  i.loading_time,
                                          'distance': i.route[j-1].distances['Distance'][i.route[j-1].distances['Destination'] == i.route[j].name].values[0],
                                          'resource_speed': vessel_speed,
                                          'evacuees': i.passengers_route[j-1]}, ignore_index = True)
            route_segment_id += 1
        
    return(route_details)

