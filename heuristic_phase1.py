"""
@fiete
November 12, 2020
"""

# import packages
import pandas as pd
from itertools import product 

# import modules
from location import Location
from evacLocation import EvacLocation
from dock import Dock
from evacRes import EvacRes
from generate_outputs import generate_results_table

def heuristic_phase_1(resources, island_locations, mainland_locations, island_docks, mainland_docks, upper_time_limit):
    """
    This function defines the first phase of the heuristic to geneate an initial feasible solution.
    It takes all objects of the network as inputs
    """
    
    # Default settings
    demand_left = False 
    route_list = [] # hold a list of routes available
    
    # check whether any evacuees are present at the island locations, if yes, set demand_left to true, if not, stay with default settings
    for i in island_locations:
        if i.current_evacuees.item() != 0:
            demand_left = True
            
    # identify how much demand exists after this iteration
    demand = 0
    for a in island_locations:
        demand = demand + a.current_evacuees#[0]
    # print("Remaining demand:", demand[0])
    if demand == 0:
        demand_left = False
        # print("All evacuees are allocated to a resource!")
    
    # while there is demand left or not all resources are back at shelters, keep iterating
    while (demand_left == True):
        
        # print("")
        # print("######################")
        
        # sort evacuation resources by total number of current movements and current route time, 
        # prioritizing the current route time and non-decreasing
        resources.sort(key=lambda x: (x.current_route_time, x.current_number_movements), reverse=False)
        
        ### START PREDICTING ###
        
        candidates_for_next_step = pd.DataFrame() # hold a candidate data frame that holds the next frame
        
        for k in resources:

            # collect all compatible pick_ups
            compatible_pick_ups = []
            for i in island_docks:
                # find the corresponding location
                evacuation_location = next((x for x in island_locations if (x.name == i.location)), None)
                # append if compatible with k and if evacuees left
                if (k.name in i.compatibility) and (evacuation_location.current_evacuees > 0):
                    compatible_pick_ups.append(i.name)
            
            # collect all compatible drop_offs
            compatible_drop_offs = []
            for i in mainland_docks:
                if k.name in i.compatibility:
                    compatible_drop_offs.append(i.name)
                    
            if not compatible_pick_ups:
                #print('No compatible pick up nodes with demand remain for resource ' + k.name + '. All demand on compatible nodes has already been allocated.')
                pass
            else:

                # if len(k.route) > 1:

                #     ######### 12/09/20 - adding recursive check

                #     # create a data frame that collects potential distances and expected route times
                #     kspec_list = pd.DataFrame(list(product(compatible_drop_offs, compatible_pick_ups, compatible_drop_offs)), columns=['origin', 'pick_up', 'drop_off'])
                #     kspec_list['resource'] = [k.name for i in range(len(kspec_list))]
                #     kspec_list['distance'] = [0.0 for i in range(len(kspec_list))]
                #     kspec_list['exp_route_time'] = [0.0 for i in range(len(kspec_list))]
                #     for i in range(len(kspec_list)):
                #         # print(i)
                #         better_origin_dock = next((x for x in mainland_docks if (x.name == kspec_list['origin'].iloc[i])), None)
                #         dist_to_origin_dock = k.route[-2].distances['Distance'][k.route[-2].distances['Destination'] == better_origin_dock.name].values
                #         pick_dock = next((x for x in island_docks if (x.name == kspec_list['pick_up'].iloc[i])), None)
                #         dist_to_pick_dock = better_origin_dock.distances['Distance'][better_origin_dock.distances['Destination'] == pick_dock.name].values
                #         dist_to_drop_dock = pick_dock.distances['Distance'][pick_dock.distances['Destination'] == kspec_list['drop_off'].iloc[i]].values
                #         kspec_list.loc[i,'distance'] = dist_to_origin_dock + dist_to_pick_dock + dist_to_drop_dock 
                #         # make sure that this entry only gets added if the expected route time is less than the maximum route time, else delete the entry
                #         # select the entry with the best expected route time                            
                #         if ((k.current_route_time - k.loading_time - k.route[-2].distances['Distance'][k.route[-2].distances['Destination'] == better_origin_dock.name].values) 
                #             + k.loading_time * 2 + (dist_to_pick_dock/k.vmax) * 60 + (dist_to_drop_dock/k.vloaded) * 60) <= upper_time_limit:
                #             # candidate = kspec_list[kspec_list['exp_route_time'] == min(kspec_list['exp_route_time'])]                               
                #             kspec_list.loc[i,'exp_route_time'] = (k.current_route_time - k.loading_time - k.route[-2].distances['Distance'][k.route[-2].distances['Destination'] == better_origin_dock.name].values) + k.loading_time * 2 + (dist_to_pick_dock/k.vmax) * 60 + (dist_to_drop_dock/k.vloaded) * 60
                                    
                #     # print(kspec_list)
                #     kspec_list['exp_route_time'] = kspec_list['exp_route_time'].astype(float)
                #     kspec_list = kspec_list[kspec_list['exp_route_time'] > 0.0]
                #     # print(kspec_list)
                    
                #     if kspec_list.empty:
                    
                #         # print("Additional routes on resource", k.name, "would violate max time constraint.")
                #         pass
                    
                #     else:
                    
                #         # select the entry with the best expected route time
                #         candidate = kspec_list[kspec_list['exp_route_time'] == min(kspec_list['exp_route_time'])]

                #         # append to the list of candidates for the next step
                #         candidates_for_next_step = pd.concat([candidates_for_next_step, candidate]) 
                    


                    ######### 12/09/20 - ending recursive check

                # else:
                    
                # create a data frame that collects potential distances and expected route times
                kspec_list = pd.DataFrame(list(product(compatible_pick_ups, compatible_drop_offs)), columns=['pick_up', 'drop_off'])
                kspec_list['resource'] = [k.name for i in range(len(kspec_list))]
                kspec_list['distance'] = [0.0 for i in range(len(kspec_list))]
                kspec_list['exp_route_time'] = [0.0 for i in range(len(kspec_list))]
                for i in range(len(kspec_list)):
                    pick_dock = next((x for x in island_docks if (x.name == kspec_list['pick_up'].iloc[i])), None)
                    dist_to_pick_dock = k.current_dock.distances['Distance'][k.current_dock.distances['Destination'] == pick_dock.name].values
                    dist_to_drop_dock = pick_dock.distances['Distance'][pick_dock.distances['Destination'] == kspec_list['drop_off'].iloc[i]].values
                    kspec_list.loc[i,'distance'] = dist_to_pick_dock + dist_to_drop_dock
                    # make sure that this entry only gets added if the expected route time is less than the maximum route time, else delete the entry
                    # select the entry with the best expected route time                            
                    if (k.current_route_time + k.loading_time * 2 + (dist_to_pick_dock/k.vmax) * 60 + (dist_to_drop_dock/k.vloaded) * 60) <= upper_time_limit:
                        # candidate = kspec_list[kspec_list['exp_route_time'] == min(kspec_list['exp_route_time'])]                               
                        kspec_list.loc[i,'exp_route_time'] = k.current_route_time + k.loading_time * 2 + (dist_to_pick_dock/k.vmax) * 60 + (dist_to_drop_dock/k.vloaded) * 60
                            
                # print(kspec_list)
                kspec_list['exp_route_time'] = kspec_list['exp_route_time'].astype(float)
                kspec_list = kspec_list[kspec_list['exp_route_time'] > 0.0]
                # print(kspec_list)
                
                if kspec_list.empty:
                
                    # print("Additional routes on resource", k.name, "would violate max time constraint.")
                    pass
                
                else:
                
                    # select the entry with the best expected route time
                    candidate = kspec_list[kspec_list['exp_route_time'] == min(kspec_list['exp_route_time'])]

                    # append to the list of candidates for the next step
                    candidates_for_next_step = pd.concat([candidates_for_next_step, candidate]) 
        
        # print(candidates_for_next_step)

        if not candidates_for_next_step.empty:
        
            # FINISH PREDICTING

            ###### 12/09/20 Check better previous step
            # Now select the candidate with the lowest expexted route time and implement it in the objects
            next_step_data = candidates_for_next_step[candidates_for_next_step['exp_route_time'] == min(candidates_for_next_step['exp_route_time'])]
            next_resource = next((x for x in resources if (x.name == next_step_data['resource'].iloc[0])), None)
            # print('Resource selected for next step:', next_resource.name)

            # update the locations
            # if len(next_resource.route) > 1:
            #     replace_origin = next((x for x in mainland_docks if (x.name == next_step_data['origin'].iloc[0])), None)
            next_pick_up = next((x for x in island_docks if (x.name == next_step_data['pick_up'].iloc[0])), None)
            next_pick_up_loc = next((x for x in island_locations if (x.name == next_pick_up.location)), None)
            if next_pick_up_loc.current_evacuees > next_resource.max_cap:
                load = next_resource.max_cap
                next_pick_up_loc.current_evacuees = next_pick_up_loc.current_evacuees - load
            else:
                load = next_pick_up_loc.current_evacuees[0]
                next_pick_up_loc.current_evacuees = 0

            # update the resource
            # if len(next_resource.route) > 1:
            #     next_resource.route[-1] = next((x for x in mainland_docks if (x.name == next_step_data['origin'].iloc[0])), None)
            next_resource.route.append(next((x for x in island_docks if (x.name == next_step_data['pick_up'].iloc[0])), None)) # update route with route segment
            next_resource.passengers_route.append(0)
            next_resource.route.append(next((x for x in mainland_docks if (x.name == next_step_data['drop_off'].iloc[0])), None)) # update route with route segment
            next_resource.passengers_route.append(load)
            next_resource.current_number_movements += 2
            next_resource.current_dock = next((x for x in mainland_docks if (x.name == next_step_data['drop_off'].iloc[0])), None) # update to end of next route segment
            next_resource.update_route_time(island_docks, mainland_docks)

            # identify how much demand exists after this iteration
            demand = 0
            for a in island_locations:
                demand = demand + a.current_evacuees#[0]
#             print("Remaining demand:", demand[0])
            if demand == 0:
                demand_left = False
#                 print("All evacuees are allocated to a resource!")

                
        else:
            demand_left = False
            # print("It is not possible to evacuate the entire population with this fleet.")
    
    if resources: 
        max_route_time = 0.0
        for i in resources: 
            i.update_route_time(island_docks, mainland_docks)
            if (i.current_route_time > max_route_time) and (i.current_number_movements > 0): # only count resources that are actually used
                max_route_time = i.current_route_time
    #     print('Max route time:', max_route_time)
    
#     for i in resources:
#         print(i.name)
#         print(i.current_route_time)
#         for j in i.route:
#             print(j.name)
            
    # print final performacne metrics
#     print("------------")
#     print("RESULTS")
#     print('maximum route time for initial feasible solution:', max_route_time)
            
    # generate printable results
    route_details = generate_results_table(resources)

    evacuees_left_behind = 0
    for i in island_locations:
        evacuees_left_behind += i.current_evacuees

    # print(route_details)
        
    return(route_details, resources, island_locations, mainland_locations, island_docks, mainland_docks, max_route_time, evacuees_left_behind)