"""
@fiete
November 12, 2020
"""

# import packages
import pandas as pd
import pickle

# import other modules
from location import Location
from evacLocation import EvacLocation
from dock import Dock
from evacRes import EvacRes
from generate_outputs import generate_results_table

# auxiliary functions

def save_current_resource_set(resources):
    """
    This function creates a snap shot of the current resource sets and saves them to a file.
    We can recover these objects later if we realize that a new solution is not an improvement to the old one. 
    """
    
    # generate lists of objects in dictionary form
    resource_saver = []
    for i in resources:
        resource_saver.append(vars(i))

    # save the resources to an external file
    for i in resource_saver:
        filename = 'resource_current_state_' + str(i['name'])
        outfile = open(filename, 'wb')
        pickle.dump(i, outfile)
        outfile.close()
    
    return(resource_saver)


def recover_previous_resource_set(resource_saver, resources):
    """
    This function recovers a previous state of resources from files.
    This is useful to recover a previous solution if the new solution is not better
    """

    # read the resources from an external file
    for i in resource_saver:
        filename = 'resource_current_state_' + str(i['name'])
        infile = open(filename, 'rb')
        i = pickle.load(infile) # overwrite
        resource = next((t for t in resources if t.name == i['name']), None)
        resource.recover_previous_parameters(i)
        infile.close()
    
    return(resource_saver, resources)


def calculate_fix_cost(resources):
    """
    An auxiliary function to calculate the fixed cost of an evacuation plan
    """
    cost = 0
    for i in resources:
        cost += i.contract_cost
        
    return(cost)


def calculate_variable_cost(resources):
    """
    An auxiliary function to calculate the operating cost of an evacuation plan.
    """
    cost = 0
    for i in resources:
        cost += i.operating_cost * ((i.current_route_time - i.time_to_availability)/60)
        
    return(cost)


def calculate_remaining_evacuees(island_locations):
    """
    An auxiliary function to calcluate the people left behind.
    """
    remaining_evacuees = 0
    for i in island_locations:
        remaining_evacuees += i.current_evacuees
        
    return(remaining_evacuees)
    

def heuristic_phase_2(route_details, resources, island_locations, mainland_locations, island_docks, mainland_docks, max_route_time, upper_time_limit):
    """
    A local search procedure to improve the solution obtained by the heuristic in phase 1 of the algorithm.
    """
    
    # at first introduce two variables that indicate whether an improvmenet has been found or not. 
    # these are set as true initially such that the inital loop will be entered.
    remainder_from_phase1_imp_found = True
    re_allocate_improvement_found = True
    swap_improvement_found = True
    
    while (re_allocate_improvement_found == True) or (swap_improvement_found == True) or (remainder_from_phase1_imp_found == True):

        print("new iteration")
        
        """-----PART A: CHECK RE-ALLOCATION OF REMAINING PASSENGERS-----"""
        
        """LEVEL 1: TEST RE-ALLOCATION PASSENGERS LEFT BEHIND FROM PHASE 1"""
        
        # at first set the improvement found variables to false, to trigger a change if an improvement has been found
        remainder_from_phase1_imp_found = False
        re_allocate_improvement_found = False
        swap_improvement_found = False
        
        # find locations that still have demand left
        locs_remaining_demand = []
        for i in island_locations:
            if i.current_evacuees > 0:
                locs_remaining_demand.append(i)
                    
        # only execute this step if there is remaining evacuation demand
        if locs_remaining_demand:
        
            remainder_checked = False # a new variable to mark whether re-allocation has been checked

            # save the current setup to file 
            resource_saver = save_current_resource_set(resources) # save the files

            # now test the re allocation of remaining passengers to another resource
            while remainder_checked == False:

                """LEVEL 1: STEP 1: SELECT AFFECTED LOCATION"""
                
                locs_remaining_demand.sort(key=lambda x: (x.current_evacuees), reverse=False)
                
                # try re-allocating for every element in the list
                for t in locs_remaining_demand:

                    # define a variable that will indicate the swap resource index and initialize at zero
                    x = 0

                    # Define alternative resources compatible with the pick up location at which we find this pick-up node
                    pick_up_nodes_in_area = [x for x in island_docks if (x.location == t.name)]
                    alternative_resources = [] # a new list to hold the alternative resources
                    for i in pick_up_nodes_in_area:
                        for j in resources:
                            if (j.name in i.compatibility) and (j not in alternative_resources):
                                alternative_resources.append(j)

                    # Define a new variable of re-allocation of the (n-k)th route
                    re_allocation_of_passengers_at_t_not_possible = False

                    demand_to_be_re_distributed = t.current_evacuees
                    demand_tester = demand_to_be_re_distributed

                    # save the current setup to file 
                    resource_saver = save_current_resource_set(resources) # save the files

                    # introduce a varaible that checks whether there was a small improvement found
                    small_improvement_found = False

                    while (re_allocation_of_passengers_at_t_not_possible == False) and (demand_to_be_re_distributed > 0):

                        """LEVEL 1: STEP 2a: CHECK EXTRA CAPACITY AT SAME LOCATION"""

                        # check the list of resources whether any of them, has extra capacity available at the same pick up location
                        comp_trips_with_extra_cap = []
                        for j in resources:
                            locations = [x.location for x in j.route]
                            for i in locations:
                                if (t.name == i) and (j.passengers_route[locations.index(i)] < j.max_cap):
                                    comp_trips_with_extra_cap.append([j.name, locations.index(i), j.passengers_route[locations.index(i)]])
                        # print(comp_trips_with_extra_cap)

                        # if extra capacity is available, re allocate some of the passengers, else do nothing            
                        if not comp_trips_with_extra_cap:
                            pass

                        else:
                            for i in comp_trips_with_extra_cap:
                                # print("This is happening...")
                                extra_cap_resource = next((x for x in alternative_resources if (x.name == i[0])), None)
                                if demand_tester > (extra_cap_resource.max_cap - extra_cap_resource.passengers_route[i[1]]):
                                    load = extra_cap_resource.max_cap - extra_cap_resource.passengers_route[i[1]]
                                    demand_tester = demand_tester - load
                                else:
                                    load = demand_tester
                                    demand_tester = 0
                                extra_cap_resource.passengers_route[i[1]] += load
                                # print(load[0], 'passengers allocated to', extra_cap_resource.name, 'to an existing trip')
                                t.current_evacuees = t.current_evacuees - load

                        """LEVEL 1: STEP 2b: SELECT SWAP RESOURCE"""

                        # # # only continue if there is still demand left after checking for re-allocation without additional routes
                        # if demand_tester > 0:

                        #     # sort alternative resources by current route time in ascending order
                        #     # resources.sort(key=lambda x: (x.current_route_time, x.current_number_movements), reverse=False) # sort resources

                        #     if len(alternative_resources) > 0:
                        #         # choose the swap resource
                        #         swap_resource = alternative_resources[x]
                        #         # print("The current swap resource is:", swap_resource.name) 

                        #         # test a re-allocation of the routes
                        #         # at first the swap resource

                        #         compatible_pick_ups = []
                        #         for i in island_docks:
                        #             if swap_resource.name in i.compatibility:
                        #                 compatible_pick_ups.append(i.name)

                        #         # find the closes compatible pick up node at the location for the swap resource:
                        #         # create a data frame that collects potential distances and expected route times
                        #         kpick_list = pd.DataFrame(list(compatible_pick_ups), columns=['drop_off'])
                        #         kpick_list['distance'] = [0.0 for i in range(len(kpick_list))]
                        #         kpick_list['exp_route_time'] = [0.0 for i in range(len(kpick_list))]
                        #         for i in range(len(kpick_list)):
                        #             pick_dock = next((x for x in island_docks if (x.name == kpick_list['drop_off'].iloc[i])), None)
                        #             dist_to_pick_dock = swap_resource.current_dock.distances['Distance'][swap_resource.current_dock.distances['Destination'] == pick_dock.name].values
                        #             kpick_list.loc[i,'distance'] = dist_to_pick_dock
                        #             kpick_list.loc[i,'exp_route_time'] = swap_resource.loading_time + (dist_to_pick_dock/swap_resource.vloaded) * 60

                        #         # select the entry with the best expected route time
                        #         candidate = kpick_list[kpick_list['exp_route_time'] == min(kpick_list['exp_route_time'])]
                        #         new_pick_up_node = next((x for x in island_docks if (x.name == candidate['drop_off'].iloc[0])), None)

                        #         swap_resource.route.append(new_pick_up_node) # append the new pick up node at the end 
                        #         swap_resource.current_dock = new_pick_up_node
                        #         swap_resource.update_route_time(island_docks, mainland_docks)
                        #         swap_resource.passengers_route.append(0) # append the passenger volume for the trip to the pick up node

                        #         # calculate next step in drop off

                        #         compatible_drop_offs = []
                        #         for i in mainland_docks:
                        #             if swap_resource.name in i.compatibility:
                        #                 compatible_drop_offs.append(i.name)

                        #         # find the closes compatible drop off node for the swap resource:
                        #         # create a data frame that collects potential distances and expected route times
                        #         kspec_list = pd.DataFrame(list(compatible_drop_offs), columns=['drop_off'])
                        #         kspec_list['distance'] = [0.0 for i in range(len(kspec_list))]
                        #         kspec_list['exp_route_time'] = [0.0 for i in range(len(kspec_list))]
                        #         for i in range(len(kspec_list)):
                        #             drop_dock = next((x for x in mainland_docks if (x.name == kspec_list['drop_off'].iloc[i])), None)
                        #             dist_to_drop_dock = swap_resource.current_dock.distances['Distance'][swap_resource.current_dock.distances['Destination'] == drop_dock.name].values
                        #             kspec_list.loc[i,'distance'] = dist_to_drop_dock
                        #             kspec_list.loc[i,'exp_route_time'] = swap_resource.loading_time + (dist_to_drop_dock/swap_resource.vloaded) * 60

                        #         # select the entry with the best expected route time
                        #         if len(kspec_list) > 1:
                        #             candidate = kspec_list[kspec_list['exp_route_time'] == min(kspec_list['exp_route_time'])]
                        #             new_drop_off_node = next((x for x in mainland_docks if (x.name == candidate['drop_off'].iloc[0])), None)

                        #             swap_resource.route.append(new_drop_off_node) # append the new drop off node at the end
                        #             swap_resource.current_dock = new_drop_off_node

                        #             if demand_tester > swap_resource.max_cap:
                        #                 load_re = swap_resource.max_cap
                        #                 demand_tester = demand_tester - load_re
                        #             else:
                        #                 load_re = demand_tester
                        #                 demand_tester = 0

                        #             swap_resource.passengers_route.append(load_re) # append the passenger volume for the trip to the drop off node
                        #             swap_resource.update_route_time(island_docks, mainland_docks)

                        #         else:
                        #             pass

                        #     else:
                        #         # print("No alternative resources are available.")
                        #         pass

                        # calculate the new max route time
                        new_route_time = 0.0
                        for i in resources: 
                            if (i.current_route_time > new_route_time) and (i.current_number_movements > 0): # only count resources that are actually used
                                new_route_time = i.current_route_time
                        # print("Proposed new route time:", new_route_time)
                        

                        # if the new route time is larger than the max route time, re-instate the previous solution
                        if new_route_time >= upper_time_limit:
                            # recover resources
                            # print("New route not accepted! No improvement!")
                            # print("Recovering previous solution!")
                            resource_saver, resources = recover_previous_resource_set(resource_saver, resources)
                            demand_tester = demand_to_be_re_distributed
                            # small_improvement_found = False


                        if (new_route_time < upper_time_limit) and (new_route_time < max_route_time):
                            demand_to_be_re_distributed = demand_tester
                            remainder_from_phase1_imp_found = True
                            small_improvement_found = True
                            remainder_checked = True
                            # print("New route time accepted at:", new_route_time)
                            # print("Remaining demand to be re-distributed:", demand_tester)
                            
                            max_route_time = new_route_time
                            t.current_evacuees = t.current_evacuees - load_re
                            # print(load_re[0], 'passengers allocated to resource', swap_resource.name, 'through an additional trip')
                            resource_saver = save_current_resource_set(resources)

                        # increase the index counter for the swap resource selection
                        x += 1

                        if x >= (len(alternative_resources)) and (small_improvement_found == True):

                            x = 0 # restart from beginning of swap resource list
                            small_improvement_found = False

                        if x >= (len(alternative_resources)) and (small_improvement_found == False):

                            """CLOSE LEVEL 2"""

                            re_allocation_of_passengers_at_t_not_possible = True
                            # print("Re-allocation of these passengers is not possible.")
                            # recover the previous settings

                            resource_saver, resources = recover_previous_resource_set(resource_saver, resources)
                            remainder_checked = True
        
        """-----PART B: CHECK RE-ALLOCATION-----"""
        
        """LEVEL 1: TEST RE-ALLOCATION OF ROUTES"""
        
        # at first set the improvement found variables to false, to trigger a change if an improvement has been found
        re_allocate_improvement_found = False
        
        # print("Testing re-allocation of routes...")
        
        re_allocation_checked = False # a new variable to mark whether re-allocation has been checked
        
        # save the current setup to file 
        resource_saver = save_current_resource_set(resources) # save the files
        
        # initialize the number of steps from the last route on the limiting resource 
        k = 1
        
        # now test the re allocation of a route to another resource
        while re_allocation_checked == False:
            
            """LEVEL 1: STEP 1: SELECT LIMITING ROUTE"""
            
            resources.sort(key=lambda x: (x.current_route_time, x.current_number_movements), reverse=False) # sort resources
            
            # declare a variable that determines whether a limiting resource has been found
            limiting_resource_found = False
            no_other_resources_found = False
            
            # index of the resource withthe longest route time:
            i = -1
            
            # test whether the limiting resource actually is used
            while (limiting_resource_found == False) and (no_other_resources_found == False):
                
                # select the limiting resource
                # print(resources)
                limiting_resource = resources[i] # select the last one as limiting
                if len(limiting_resource.route) < 2:
                    i -= 1
                    # stop iterating if there is no other resource in the list to befound
                    try:
                        resources[i]
                    except IndexError:
                        # print('No better solution possible than what was generated in phase 1')
                        no_other_resources_found = True
                        re_allocation_checked = True

                else:
                    limiting_resource_found = True
                    # print("The limiting resource is: ", limiting_resource.name)

            # only continue if a limiting resource was found
            if limiting_resource_found == True:
            
                # define a variable that will indicate the swap resource index and initialize at zero
                x = 0
                
                # initialize the number of routes on the limiting resource
                n = len(limiting_resource.route)
                
                # # initialize the number of steps from the last route on the limiting resource 
                # k = 1
                
                # Let the (n-k)th route assigned to the limiting resource be the limiting route
                limiting_drop_off_node = limiting_resource.route[n-k]
                limiting_pick_up_node = limiting_resource.route[n-k-1]
                
                # Define alternative resources compatible with the pick up location at which we find this pick-up node
                pick_up_location = limiting_pick_up_node.location
                pick_up_nodes_in_area = [x for x in island_docks if (x.location == pick_up_location)]
                alternative_resources = [] # a new list to hold the alternative resources
                for i in pick_up_nodes_in_area:
                    for j in resources:
                        if (j.name in i.compatibility) and (j not in alternative_resources) and (j != limiting_resource):
                            alternative_resources.append(j)
                            
                # Define a new variable of re-allocation of the (n-k)th route
                re_allocation_of_nkth_route_not_possible = False
                
                # a variable determining whether the data from the limiting resource has already been dropped
                limiting_resource_data_dropped = False
                
                demand_to_be_re_distributed = limiting_resource.passengers_route[n-k-1]
                demand_tester = demand_to_be_re_distributed
                # print("Demand to be redistributed at location", pick_up_location, ":", demand_to_be_re_distributed)
                
                # save the current setup to file 
                # resource_saver = save_current_resource_set(resources) # save the files

                # introduce a varaible that checks whether there was a small improvement found
                small_improvement_found = False
                
                while (re_allocation_of_nkth_route_not_possible == False) and (demand_to_be_re_distributed > 0):
                    
                    """LEVEL 1: STEP 2a: CHECK EXTRA CAPACITY AT SAME LOCATION"""
                    
                    # check the list of resources whether any of them, has extra capacity available at the same pick up location
                    comp_trips_with_extra_cap = []
                    for j in alternative_resources:
                        locations = [x.location for x in j.route]
                        for i in locations:
                            if (pick_up_location == i) and (j.passengers_route[locations.index(i)] < j.max_cap):
                                comp_trips_with_extra_cap.append([j.name, locations.index(i), j.passengers_route[locations.index(i)]])
                                
                    # if extra capacity is available, re allocate some of the passengers, else do nothing            
                    if not comp_trips_with_extra_cap:
                        # print('No extra capacity on other resources available')
                        pass
                    
                    else:
                        # print('Extra capacity at other resources existing.')
                        for i in comp_trips_with_extra_cap:
                            extra_cap_resource = next((x for x in alternative_resources if (x.name == i[0])), None)
                            if demand_tester > (extra_cap_resource.max_cap - extra_cap_resource.passengers_route[i[1]]):
                                load = extra_cap_resource.max_cap - extra_cap_resource.passengers_route[i[1]]
                                demand_tester = demand_tester - load
                            else:
                                load = demand_tester
                                demand_tester = 0
                            extra_cap_resource.passengers_route[i[1]] += load
                            # print(load, 'passengers re-allocated to', extra_cap_resource.name)
                            
                        # if the remaining demand on the resource is now completely re-allocated,
                        # delete the route from the limiting resource and update it s route time
                        if demand_tester == 0 and limiting_resource_data_dropped == False:

                            del limiting_resource.route[n-k] # delete the entries that have been re-allocated
                            del limiting_resource.route[n-k-1] # delete the entries that have been re-allocated

                            del limiting_resource.passengers_route[n-k-1] # delete the entries that have been re-allocated
                            del limiting_resource.passengers_route[n-k-2] # delete the entries that have been re-allocated

                            limiting_resource.update_route_time(island_docks, mainland_docks) # update the route time

                            limiting_resource_data_dropped = True # update the fact that the limiting resource has been dropped
                            # print("Deleted last step of limiting route.")
                        else:
                            limiting_resource.passengers_route[n-k-1] = limiting_resource.passengers_route[n-k-1] - load
                    
                    """LEVEL 1: STEP 2b: SELECT SWAP RESOURCE"""
                    
                    # only continue if there is still demand left after checking for re-allocation without additional routes
                    if demand_tester > 0:
                    
                        # sort alternative resources by current route time in ascending order
                        alternative_resources.sort(key=lambda x: (x.current_route_time, x.current_number_movements), reverse=False) # sort resources

                        if not alternative_resources:
                            # print('No alternative resources available for this route.')
                            pass

                        else:
                            # print('Demand is still there:', demand_tester)

                            # choose the swap resource
                            swap_resource = alternative_resources[x]
                            # print("The current swap resource is:", swap_resource.name) 

                            # test a re-allocation of the routes
                            # at first the swap resource

                            swap_resource.route.append(limiting_pick_up_node) # append the new pick up node at the end 
                            swap_resource.current_dock = limiting_pick_up_node
                            swap_resource.update_route_time(island_docks, mainland_docks)
                            swap_resource.passengers_route.append(0) # append the passenger volume for the trip to the pick up node

                            compatible_drop_offs = []
                            for i in mainland_docks:
                                if swap_resource.name in i.compatibility:
                                    compatible_drop_offs.append(i.name)

                            # find the closes compatible drop off node for the swap resource:
                            # create a data frame that collects potential distances and expected route times
                            kspec_list = pd.DataFrame(list(compatible_drop_offs), columns=['drop_off'])
                            kspec_list['distance'] = [0.0 for i in range(len(kspec_list))]
                            kspec_list['exp_route_time'] = [0.0 for i in range(len(kspec_list))]
                            for i in range(len(kspec_list)):
                                drop_dock = next((x for x in mainland_docks if (x.name == kspec_list['drop_off'].iloc[i])), None)
                                dist_to_drop_dock = swap_resource.current_dock.distances['Distance'][swap_resource.current_dock.distances['Destination'] == drop_dock.name].values
                                kspec_list.loc[i,'distance'] = dist_to_drop_dock
                                kspec_list.loc[i,'exp_route_time'] = swap_resource.loading_time + (dist_to_drop_dock/swap_resource.vloaded) * 60

                            # select the entry with the best expected route time
                            candidate = kspec_list[kspec_list['exp_route_time'] == min(kspec_list['exp_route_time'])]
                            new_drop_off_node = next((x for x in mainland_docks if (x.name == candidate['drop_off'].iloc[0])), None)

                            swap_resource.route.append(new_drop_off_node) # append the new drop off node at the end
                            swap_resource.current_dock = new_drop_off_node

                            if demand_tester > swap_resource.max_cap:
                                load = swap_resource.max_cap
                                demand_tester = demand_tester - load
                            else:
                                load = demand_tester
                                demand_tester = 0

                            swap_resource.passengers_route.append(load) # append the passenger volume for the trip to the drop off node
                            swap_resource.update_route_time(island_docks, mainland_docks)

                            # at second the limiting resource

                            if (demand_tester == 0) and (limiting_resource_data_dropped == False):

                                # print("Length:", len(limiting_resource.route))
                                # print("Index to be used:", n-k)
                                del limiting_resource.route[n-k] # delete the entries that have been re-allocated
                                del limiting_resource.route[n-k-1] # delete the entries that have been re-allocated

                                del limiting_resource.passengers_route[n-k-1] # delete the entries that have been re-allocated
                                del limiting_resource.passengers_route[n-k-2] # delete the entries that have been re-allocated

                                limiting_resource.update_route_time(island_docks, mainland_docks) # update the route time

                                limiting_resource_data_dropped = True # update the fact that the limiting resource has been dropped

                            else:
                                limiting_resource.passengers_route[n-k-1] = limiting_resource.passengers_route[n-k-1] - load

                    # calculate the new max route time
                    new_route_time = 0.0
                    for i in resources: 
                        if (i.current_route_time > new_route_time) and (i.current_number_movements > 0): # only count resources that are actually used
                            new_route_time = i.current_route_time
                    # print("Proposed new route time:", new_route_time)
                    # print("Remaining demand to be re-distributed:", demand_tester)

                    # if the new route time is larger than the max route time, re-instate the previous solution
                    if new_route_time >= max_route_time:
                        # recover resources
                        # print("New route not accepted! No improvement!")
                        # print("Recovering previous solution!")
                        resource_saver, resources = recover_previous_resource_set(resource_saver, resources)
                        demand_tester = demand_to_be_re_distributed
                        limiting_resource_data_dropped = False # update the limiting resource data drop
                        # small_improvement_found = False
                        

                    if (new_route_time < max_route_time) and (demand_tester == 0):
                        demand_to_be_re_distributed = demand_tester
                        re_allocate_improvement_found = True
                        small_improvement_found = True
                        # print("New route time accepted at:", new_route_time)
                        max_route_time = new_route_time
                        resource_saver = save_current_resource_set(resources) # TESTING THIS ONLY RIGHT NOW


                    # print the current status:
                    # print('#############')
                    # print('Current best route time:', max_route_time)
                    # print('Remaining demand:', demand_tester)
                    # for i in resources:
                    #     print(i.name)
                    #     print("Route time:", i.current_route_time)
                    #     for j in i.passengers_route:
                    #         print(j)
                    #     for j in i.route:
                    #         print(j.name)
                                
                    # increase the index counter for the swap resource selection
                    x += 1
                    
                    if x >= (len(alternative_resources)) and (small_improvement_found == True):
                        
                        x = 0 # restart from beginning of swap resource list
                        small_improvement_found = False
                    
                    if x >= (len(alternative_resources)) and (small_improvement_found == False):
                        
                        """CLOSE LEVEL 2"""
                        
                        re_allocation_of_nkth_route_not_possible = True
                        # print("Re-allocation of this route is not possible.")
                        # recover the previous settings

                        resource_saver, resources = recover_previous_resource_set(resource_saver, resources)
                        k += 2 # increase the index of the route on the limiting resource to check whether we can re-allocate that to another resource
            
                        if k >= n-1:
                            
                            """CLOSE LEVEL 1"""
                            
                            re_allocation_checked = True
                            # print("Re-allocation of no route without losses of demand or increase in evacuation time possible.")
                            
        
        
        if re_allocate_improvement_found == False:

            """-----PART C: CHECK ROUTE SWAP-----"""
            
            """LEVEL 2: TEST SWAPPING OF ROUTES WITH NON-LIMITING RESOURCE"""
            
            # at first set the improvement found variables to false, to trigger a change if an improvement has been found
            swap_improvement_found = False
            
            # print("Testing swapping of routes...")
            
            swapping_checked = False # a new variable to mark whether re-allocation has been checked
            
            # save the current setup to file 
            resource_saver = save_current_resource_set(resources) # save the files
            
            # initialize the number of steps from the last route on the limiting resource 
            k = 1
            
            # now test the re allocation of a route to another resource
            while swapping_checked == False:
                
                """LEVEL 2: STEP 1: SELECT LIMITING ROUTE"""
                
                resources.sort(key=lambda x: (x.current_route_time, x.current_number_movements), reverse=False) # sort resources
                # result_list = sorted(resources, key=lambda x: (x.current_route_time, x.current_number_movements))
                # for car in result_list:
                #         print(car.name + " and route time is " + str(car.current_route_time))
                
                # declare a variable that determines whether a limiting resource has been found
                limiting_resource_found = False
                no_other_resources_found = False
                
                # index of the resource withthe longest route time:
                i = -1
                
                # test whether the limiting resource actually is used
                while (limiting_resource_found == False) and (no_other_resources_found == False):
                    
                    # select the limiting resource
                    # print(resources)
                    limiting_resource = resources[i] # select the last one as limiting
                    if len(limiting_resource.route) < 2:
                        i -= 1
                        # stop iterating if there is no other resource in the list to befound
                        try:
                            limiting_resource = resources[i]
                        except IndexError:
                            # print('No better solution possible than what was generated in phase 1')
                            no_other_resources_found = True
                            swapping_checked = True

                    else:
                        limiting_resource_found = True
                        # print("The limiting resource is: ", limiting_resource.name)

                # print("limiting resource route before")
                # for i in limiting_resource.route:
                #     print(i.name)
                # print("limiting resource passengers before", limiting_resource.passengers_route)

                # only continue if a limiting resource was found
                if limiting_resource_found == True:
                
                    # define a variable that will indicate the swap resource index and initialize at zero
                    x = 0
                    
                    # initialize the number of routes on the limiting resource
                    n = len(limiting_resource.route)
                    
                    # initialize the number of steps from the last route on the limiting resource 
                    #k = 1
                    
                    # Let the (n-k)th route assigned to the limiting resource be the limiting route
                    limiting_drop_off_node = limiting_resource.route[n-k]
                    limiting_pick_up_node = limiting_resource.route[n-k-1]
                    
                    # Define alternative resources compatible with the pick up location at which we find this pick-up node
                    pick_up_location = limiting_pick_up_node.location
                    pick_up_nodes_in_area = [x for x in island_docks if (x.location == pick_up_location)]
                    alternative_resources = [] # a new list to hold the alternative resources
                    for i in pick_up_nodes_in_area:
                        for j in resources:
                            if (j.name in i.compatibility) and (j not in alternative_resources) and (j != limiting_resource):
                                alternative_resources.append(j)
                                
                    # Define a new variable of swap of the (n-k)th route
                    swap_of_nkth_route_not_possible = False
                    
                    # define a new variable that denotes, whether a route swap has been performed
                    swap_of_nkth_route_performed = False
                    
                    # a variable determining whether the data from the limiting resource has already been dropped
                    limiting_resource_data_dropped = False
                    
                    demand_to_be_re_distributed = limiting_resource.passengers_route[n-k-1]
                    demand_tester = demand_to_be_re_distributed
                    # print("Demand to be redistributed at location", pick_up_location, ":", demand_to_be_re_distributed)
                    
                    # save the current setup to file 
                    resource_saver = save_current_resource_set(resources) # save the files
                    
                    while (swap_of_nkth_route_not_possible == False) and (swap_of_nkth_route_performed == False) and (demand_to_be_re_distributed > 0):
                        
                        """LEVEL 2: STEP 2: SELECT SWAP RESOURCE"""
                        
                        # sort alternative resources by current route time in ascending order
                        alternative_resources.sort(key=lambda x: (x.current_route_time, x.current_number_movements), reverse=False) # sort resources
                        
                        if not alternative_resources:
                            # print('No alternative resources available for this route.')
                            swap_of_nkth_route_not_possible = True
                            swap_improvement_found = False
                            swapping_checked = True
                            
                        else:
                                
                            swap_resource_found = False
                            no_other_swap_resources_found = False

                            # test whether the limiting resource actually is used
                            while (swap_resource_found == False) and (no_other_swap_resources_found == False):
                                
                                # select the limiting resource
                                # print(resources)
                                try:
                                    swap_resource = alternative_resources[x] # select the last one as limiting
                                    m = len(swap_resource.route)
                                    if m < 2:
                                        x += 1
                                        # stop iterating if there is no other resource in the list to befound
                                        try:
                                            swap_resource = alternative_resources[x]
                                        except IndexError:
                                            # print('No better solution possible than what was generated in phase 1')
                                            no_other_swap_resources_found = True
                                            swapping_checked = True
                                            swap_of_nkth_route_not_possible = True

                                    else:
                                        swap_resource_found = True
                                        # print("The swap resource is: ", swap_resource.name)
                                except IndexError:
                                    # print('No better solution possible than what was generated in phase 1')
                                    no_other_swap_resources_found = True
                                    swapping_checked = True
                                    swap_of_nkth_route_not_possible = True

                            # print("The current swap resource is:", swap_resource.name)  

                            if swap_resource_found == True:

                                # print("Swap route before")
                                # for i in swap_resource.route:
                                #     print(i.name)
                                # print("Swap passengers before", swap_resource.passengers_route)
                            
                                # define a variable to traverse the steps from the last route of the swap resource
                                q = 1
                                
                                # define the demadn on the swap resource that needs to be re-distributed
                                demand_to_be_re_distributed_swap = swap_resource.passengers_route[m-q-1]
                                demand_tester_swap = demand_to_be_re_distributed_swap
                                
                                # define a variable that determines whether the swap of the limiting route with the swap resource is not possible
                                swap_of_nkth_route_with_swap_resource_not_possible = False
                                
                                # define a variable that determines whether the swap of the limiting route with the swap resource was performed
                                swap_of_nkth_route_with_swap_resource_performed = False
                                
                                # save the current setup to file 
                                resource_saver = save_current_resource_set(resources) # save the files
                                
                                while (swap_of_nkth_route_with_swap_resource_not_possible == False) and (swap_of_nkth_route_with_swap_resource_performed == False) and (demand_to_be_re_distributed_swap > 0):
                                    
                                    """LEVEL 2: STEP 3: SELECT SWAP ROUTE"""
                                    
                                    # make sure the location of the swap pick up node is not the same as the location of the limiting pick up node
                                    if (swap_resource.route[m-q-1].location != limiting_pick_up_node.location) and (swap_resource.max_cap >= demand_to_be_re_distributed) and (limiting_resource.max_cap >= demand_to_be_re_distributed_swap):
                                    
                                        # Let the (m-q)th route assigned to the swap resource be the swap route
                                        swap_drop_off_node = swap_resource.route[m-q]
                                        swap_pick_up_node = swap_resource.route[m-q-1]

                                        # check whether the limiting resource is compatible with the swap drop off node and vice versa
                                        if limiting_resource.name in swap_pick_up_node.compatibility:

                                            # print('Full compatibility of resource ' + limiting_resource.name + ' with ' + swap_pick_up_node.name + ' and ' + swap_resource.name + ' with ' + limiting_pick_up_node.name + ' ensured.')

                                            # start swapping with the swap resource
                                            swap_resource.route[m-q-1] = limiting_pick_up_node # replace the swap pick up node by the limiting pickup node
                                            swap_resource.update_route_time(island_docks, mainland_docks) # REALLY NECESARY????
                                            swap_resource.passengers_route[m-q-2] = 0 # append the passenger volume for the trip to the pick up node

                                            # identify compatible drop-offs
                                            compatible_drop_offs_swap = []
                                            for i in mainland_docks:
                                                if swap_resource.name in i.compatibility:
                                                    compatible_drop_offs_swap.append(i.name)

                                            # find the closes compatible drop off node for the swap resource:
                                            # create a data frame that collects potential distances and expected route times
                                            kspec_list_swap = pd.DataFrame(list(compatible_drop_offs_swap), columns=['drop_off'])
                                            kspec_list_swap['distance'] = [0.0 for i in range(len(kspec_list_swap))]
                                            kspec_list_swap['exp_route_time'] = [0.0 for i in range(len(kspec_list_swap))]
                                            for i in range(len(kspec_list_swap)):
                                                drop_dock = next((x for x in mainland_docks if (x.name == kspec_list_swap['drop_off'].iloc[i])), None)
                                                dist_to_drop_dock = swap_resource.route[m-q-1].distances['Distance'][swap_resource.route[m-q-1].distances['Destination'] == drop_dock.name].values
                                                kspec_list_swap.loc[i,'distance'] = dist_to_drop_dock
                                                kspec_list_swap.loc[i,'exp_route_time'] = swap_resource.loading_time + (dist_to_drop_dock/swap_resource.vloaded) * 60

                                            # select the entry with the best expected route time (greedily)
                                            candidate = kspec_list_swap[kspec_list_swap['exp_route_time'] == min(kspec_list_swap['exp_route_time'])]
                                            new_drop_off_node_swap = next((x for x in mainland_docks if (x.name == candidate['drop_off'].iloc[0])), None)

                                            swap_resource.route[m-q] = new_drop_off_node_swap # replace the existing drop_off node by the new drop off node at the end
                                            if q == 0:
                                                    swap_resource.current_dock = new_drop_off_node_swap
                                            else:
                                                pass

                                            if demand_tester > swap_resource.max_cap:
                                                load = swap_resource.max_cap
                                                demand_tester = demand_tester - load
                                            else:
                                                load = demand_tester
                                                demand_tester = 0

                                            swap_resource.passengers_route[m-q-1] = load # append the passenger volume for the trip to the drop off node
                                            swap_resource.update_route_time(island_docks, mainland_docks)

                                            # do the swap on the limiting resource

                                            limiting_resource.route[n-k-1] = swap_pick_up_node # replace the limting pick up node by the swap pickup node
                                            limiting_resource.update_route_time(island_docks, mainland_docks) # REALLY NECESARY????
                                            limiting_resource.passengers_route[n-k-2] = 0 # append the passenger volume for the trip to the pick up node

                                            # identify compatible drop-offs
                                            compatible_drop_offs_limiting = []
                                            for i in mainland_docks:
                                                if limiting_resource.name in i.compatibility:
                                                    compatible_drop_offs_limiting.append(i.name)

                                            # find the closes compatible drop off node for the limiting resource:
                                            # create a data frame that collects potential distances and expected route times
                                            kspec_list_limiting = pd.DataFrame(list(compatible_drop_offs_limiting), columns=['drop_off'])
                                            kspec_list_limiting['distance'] = [0.0 for i in range(len(kspec_list_limiting))]
                                            kspec_list_limiting['exp_route_time'] = [0.0 for i in range(len(kspec_list_limiting))]
                                            for i in range(len(kspec_list_limiting)):
                                                drop_dock = next((x for x in mainland_docks if (x.name == kspec_list_limiting['drop_off'].iloc[i])), None)
                                                dist_to_drop_dock = limiting_resource.route[n-k-1].distances['Distance'][limiting_resource.route[n-k-1].distances['Destination'] == drop_dock.name].values
                                                kspec_list_limiting.loc[i,'distance'] = dist_to_drop_dock
                                                kspec_list_limiting.loc[i,'exp_route_time'] = limiting_resource.loading_time + (dist_to_drop_dock/limiting_resource.vloaded) * 60

                                            # select the entry with the best expected route time (greedily)
                                            candidate = kspec_list_limiting[kspec_list_limiting['exp_route_time'] == min(kspec_list_limiting['exp_route_time'])]
                                            new_drop_off_node_limiting = next((x for x in mainland_docks if (x.name == candidate['drop_off'].iloc[0])), None)

                                            limiting_resource.route[n-k] = new_drop_off_node_limiting # replace the existing drop_off node by the new drop off node at the end
                                            if q == 0:
                                                    limiting_resource.current_dock = new_drop_off_node_limiting
                                            else:
                                                pass

                                            if demand_tester_swap > limiting_resource.max_cap:
                                                load = limiting_resource.max_cap
                                                demand_tester_swap = demand_tester_swap - load
                                            else:
                                                load = demand_tester_swap
                                                demand_tester_swap = 0

                                            limiting_resource.passengers_route[n-k-1] = load # append the passenger volume for the trip to the drop off node
                                            limiting_resource.update_route_time(island_docks, mainland_docks)
                                            
                                            # calculate the new max route time
                                            new_route_time = 0.0
                                            for i in resources: 
                                                if (i.current_route_time > new_route_time) and (i.current_number_movements > 0): # only count resources that are actually used
                                                    new_route_time = i.current_route_time
                                            # print("Proposed new route time:", new_route_time)

                                            # print("Limiting route after")
                                            # for i in limiting_resource.route:
                                            #     print(i.name)
                                            # print("Limiting passengers after", limiting_resource.passengers_route)
                                            # print("Swap route after")
                                            # for i in swap_resource.route:
                                            #     print(i.name)
                                            # print("Swap route after", swap_resource.passengers_route)

                                            # if the new route time is larger than the max route time, re-instate the previous solution
                                            if (new_route_time >= max_route_time) or (demand_to_be_re_distributed_swap != load):
                                                # recover resources
                                                resource_saver, resources = recover_previous_resource_set(resource_saver, resources)
                                                demand_tester = demand_to_be_re_distributed
                                                demand_tester_swap = demand_to_be_re_distributed_swap
                                                # print("New route not accepted! No improvement!")

                                            # # if the route swap led to a better solution but there is still demand left over that has not been re-distributed
                                            # # try adding routes of other resources to re-distribute this demand
                                            # if (new_route_time < max_route_time) and ((demand_tester > 0) or (demand_tester_swap > 0)):
                                            #     # print('This is a promising approach... immediate swapping led to evacuation reduction...')
                                            #     # print('Now lets try to allocate remaining demand...')
                                                
                                            #     # identify the dock that has demand left
                                            #     if demand_tester > 0:
                                            #         dock_of_interest = limiting_pick_up_node
                                            #     if demand_tester_swap > 0:
                                            #         dock_of_interest = swap_pick_up_node
                                                
                                            #     # print('Trying to re-distribute without adding further routes')
                            
                                            #     # check the list of resources whether any of them, has extra capacity available at the same pick up location
                                            #     comp_trips_with_extra_cap = []
                                            #     for j in alternative_resources:
                                            #         locations = [x.location for x in j.route]
                                            #         for i in locations:
                                            #             if (dock_of_interest.location == i) and (j.passengers_route[locations.index(i)] < j.max_cap):
                                            #                 comp_trips_with_extra_cap.append([j.name, locations.index(i), j.passengers_route[locations.index(i)]])

                                            #     # if extra capacity is available, re allocate some of the passengers, else do nothing            
                                            #     if not comp_trips_with_extra_cap:
                                            #         # print('No extra capacity on other resources available')
                                            #         pass

                                            #     else:
                                            #         for i in comp_trips_with_extra_cap:
                                            #             extra_cap_resource = next((x for x in alternative_resources if (x.name == i[0])), None)
                                            #             if demand_tester > 0:
                                            #                 if demand_tester > (extra_cap_resource.max_cap - extra_cap_resource.passengers_route[i[1]]):
                                            #                     load = extra_cap_resource.max_cap - extra_cap_resource.passengers_route[i[1]]
                                            #                     demand_tester = demand_tester - load
                                            #                 else:
                                            #                     load = demand_tester
                                            #                     demand_tester = 0
                                            #             if demand_tester_swap > 0:
                                            #                 if demand_tester_swap > (extra_cap_resource.max_cap - extra_cap_resource.passengers_route[i[1]]):
                                            #                     load = extra_cap_resource.max_cap - extra_cap_resource.passengers_route[i[1]]
                                            #                     demand_tester_swap = demand_tester_swap - load
                                            #                 else:
                                            #                     load = demand_tester_swap
                                            #                     demand_tester_swap = 0
                                            #             extra_cap_resource.passengers_route[i[1]] += load
                                            #             # print(load, 'passengers re-allocated to', extra_cap_resource.name)

                                            #     # if the remaining demand on the resource is now completely re-allocated,
                                            #     # delete the route from the limiting resource and update it s route time
                                            #     if (demand_tester == 0) and (demand_tester_swap == 0):

                                            #         # print('Extra capacity on other vessels was enough to completely satisfy excess demand.')
                                            #         demand_to_be_re_distributed = demand_tester
                                            #         re_allocate_improvement_found = True
                                            #         partially_satisfier_found = True
                                            #         # print("New route time accepted at:", new_route_time)
                                                    
                                            #     else:
                                                
                                            #         # print('Trying to add additional routes to compensate for the demand')

                                            #         # introduce a variable that indicates the index of the alternative resource
                                            #         y = 0

                                            #         # introduce a variable that records whether the remaining demand can be satsified
                                            #         satisfying_remaining_demand_impossible = False

                                            #         # introduce a variable that checks for small improvements
                                            #         partially_satisfier_found = False

                                            #         # now identify resources that can be sent there until all remaining demand is re-allocated
                                            #         while (satisfying_remaining_demand_impossible == False) and ((demand_tester > 0) or (demand_tester_swap > 0)):

                                            #             # sort alternative resources by current route time in ascending order
                                            #             alternative_resources.sort(key=lambda x: (x.current_route_time, x.current_number_movements), reverse=False) # sort resources

                                            #             # choose the swap resource
                                            #             added_resource = alternative_resources[y]
                                            #             # print("The current candidate added resource is:", added_resource.name)

                                            #             # add one route segment to the added resources
                                            #             added_resource.route.append(dock_of_interest)
                                            #             added_resource.current_dock = dock_of_interest
                                            #             added_resource.update_route_time(island_docks, mainland_docks)
                                            #             added_resource.passengers_route.append(0) # append the passenger volume for the trip to the pick up node

                                            #             # find the ending node for the added resource
                                            #             compatible_drop_offs_added = []
                                            #             for i in mainland_docks:
                                            #                 if added_resource.name in i.compatibility:
                                            #                     compatible_drop_offs_added.append(i.name)

                                            #             # find the closet compatible drop off 
                                            #             kspec_list_added = pd.DataFrame(list(compatible_drop_offs_added), columns=['drop_off'])
                                            #             kspec_list_added['distance'] = [0.0 for i in range(len(kspec_list_added))]
                                            #             kspec_list_added['exp_route_time'] = [0.0 for i in range(len(kspec_list_added))]
                                            #             for i in range(len(kspec_list_added)):
                                            #                 drop_dock = next((x for x in mainland_docks if (x.name == kspec_list_added['drop_off'].iloc[i])), None)
                                            #                 dist_to_drop_dock = added_resource.current_dock.distances['Distance'][added_resource.current_dock.distances['Destination'] == drop_dock.name].values
                                            #                 kspec_list_added.loc[i,'distance'] = dist_to_drop_dock
                                            #                 kspec_list_added.loc[i,'exp_route_time'] = added_resource.loading_time + (dist_to_drop_dock/added_resource.vloaded) * 60

                                            #             # select the entry with the best expected route time
                                            #             candidate = kspec_list_added[kspec_list_added['exp_route_time'] == min(kspec_list_added['exp_route_time'])]
                                            #             new_drop_off_node = next((x for x in mainland_docks if (x.name == candidate['drop_off'].iloc[0])), None)

                                            #             added_resource.route.append(new_drop_off_node) # append the new drop off node at the end
                                            #             added_resource.current_dock = new_drop_off_node

                                            #             if demand_tester > 0:
                                            #                 limit_allocated = True
                                            #                 swap_allocated = False
                                            #                 if demand_tester > added_resource.max_cap:
                                            #                     load = added_resource.max_cap
                                            #                     demand_tester = demand_tester - load
                                            #                 else:
                                            #                     load = demand_tester
                                            #                     demand_tester = 0
                                            #             if demand_tester_swap > 0:
                                            #                 limit_allocated = False
                                            #                 swap_allocated = True
                                            #                 if demand_tester_swap > added_resource.max_cap:
                                            #                     load = added_resource.max_cap
                                            #                     demand_tester_swap = demand_tester_swap - load
                                            #                 else:
                                            #                     load = demand_tester_swap
                                            #                     demand_tester_swap = 0

                                            #             added_resource.passengers_route.append(load) # append the passenger volume for the trip to the drop off node
                                            #             added_resource.update_route_time(island_docks, mainland_docks)

                                            #             # calculate the new max route time
                                            #             new_route_time = 0.0
                                            #             for i in resources: 
                                            #                 if (i.current_route_time > new_route_time) and (i.current_number_movements > 0): # only count resources that are actually used
                                            #                     new_route_time = i.current_route_time
                                            #             # print("Proposed new route time after adding additional resources:", new_route_time)

                                            #             # if the new route time is larger than the max route time, re-instate the previous solution
                                            #             if new_route_time >= max_route_time:
                                            #                 # recover resources
                                            #                 # print("New route not accepted! No improvement!")
                                            #                 # print("Recovering previous solution!")

                                            #                 if limit_allocated == True:
                                            #                     demand_tester = demand_tester + added_resource.passengers_route[-1]
                                            #                 elif swap_allocated == True:
                                            #                     demand_tester_swap = demand_tester_swap + added_resource.passengers_route[-1]

                                            #                 # delete the last two elements of the resource route
                                            #                 del added_resource.route[-1]
                                            #                 del added_resource.route[-1]
                                            #                 # delete the last two elements of the passengers route list
                                            #                 del added_resource.passengers_route[-1]
                                            #                 del added_resource.passengers_route[-1]

                                            #                 added_resource.update_route_time(island_docks, mainland_docks)
                                            #                 # print('Solution re-created')


                                            #             if (new_route_time < max_route_time) and (demand_tester == 0) and (demand_tester_swap == 0):

                                            #                 demand_to_be_re_distributed = demand_tester
                                            #                 re_allocate_improvement_found = True
                                            #                 partially_satisfier_found = True
                                            #                 # print("New route time accepted at:", new_route_time)

                                            #             # print the current status:
                                            #             # print('#############')
                                            #             # print('Current best route time:', max_route_time)
                                            #             # print('Remaining demand at limiting pick up node:', demand_tester)
                                            #             # print('Remaining demand at swap pick up node:', demand_tester_swap)
                                            #             # for i in resources:
                                            #             #     print(i.name)
                                            #             #     print("Route time:", i.current_route_time)
                                            #             #     for j in i.passengers_route:
                                            #             #         print(j)
                                            #             #     for j in i.route:
                                            #             #         print(j.name)

                                            #             y += 1

                                            #             if (y == len(alternative_resources)) and (partially_satisfier_found == True):

                                            #                 y = 0
                                            #                 partially_satisfier_found = False

                                            #             if (y == len(alternative_resources)) and (partially_satisfier_found == False):
                                            #                 # print("With the current set up it is not possible to fully re-distribute demand after swapping")
                                            #                 satisfying_remaining_demand_impossible = True
                                            #                 # recover the previous solution
                                            #                 resource_saver, resources = recover_previous_resource_set(resource_saver, resources)
                                            #                 demand_tester = demand_to_be_re_distributed
                                            #                 demand_tester_swap = demand_to_be_re_distributed_swap


                                                ##########################################################

                                            elif (new_route_time < max_route_time) and (demand_tester == 0) and (demand_tester_swap == 0):
                                                demand_to_be_re_distributed = demand_tester
                                                demand_to_be_re_distributed_swap = demand_tester_swap
                                                swap_of_nkth_route_with_swap_resource_performed = True
                                                swap_of_nkth_route_performed = True
                                                swap_improvement_found = True
                                                small_improvement_found = True
                                                # print("New route time accepted at:", new_route_time)
                                                max_route_time = new_route_time
                                                resource_saver = save_current_resource_set(resources) # save the files

                                            else:
                                                pass


                                            # print the current status:
                                            # print('#############')
                                            # print('Current best route time:', max_route_time)
                                            # print('Remaining demand:', demand_tester)
                                            # for i in resources:
                                            #     print(i.name)
                                            #     print("Route time:", i.current_route_time)
                                            #     for j in i.passengers_route:
                                            #         print(j)
                                            #     for j in i.route:
                                            #         print(j.name)


                                        else:
                                            # print(limiting_resource.name + ' is not compatible with ' + swap_pick_up_node.name)
                                            pass

                                    
                                    else:
                                        # print("No testing, since same location of selected pair")
                                        pass
                                    
                                    # increase the counter for q to test other routes on swap resource
                                    q = q + 2

                                    if q >= m:
                                        
                                        """CLOSE STEP 3"""
                                        swap_of_nkth_route_with_swap_resource_not_possible = True
                                        # increase counter for x to test another swap resource
                                        x += 1
                                        
                                        if x >= len(alternative_resources):
                                            
                                            """CLOSE STEP 2"""
                                            swap_of_nkth_route_not_possible = True
                                            k = k + 2
                                            
                                            if k >= n:
                                                
                                                """CLOSE LEVEL 1"""
                                                swapping_checked = True
                                                # print("Swapping of no route without losses of demand or increase in evacuation time possible.")

        print(remainder_from_phase1_imp_found)
        print(re_allocate_improvement_found)
        print(swap_improvement_found)
        print(max_route_time)
                                            
    # print final performacne metrics
    # print("------------")
    # print("RESULTS")
    # print('maximum route time after local search heuristic:', max_route_time)
    
    # generate printable results
    route_details = generate_results_table(resources)
    # print(route_details)
    
    # calculate variable operating cost
    variable_operating_cost = calculate_variable_cost(resources)
    
    # calculate the number of people left behind
    evacuees_left_behind = calculate_remaining_evacuees(island_locations)

    # calculate fixed cost of route plan
    fixed_cost = calculate_fix_cost(resources)
    
    return(route_details, resources, island_locations, mainland_locations, island_docks, 
        mainland_docks, max_route_time, variable_operating_cost, evacuees_left_behind, fixed_cost)                      

