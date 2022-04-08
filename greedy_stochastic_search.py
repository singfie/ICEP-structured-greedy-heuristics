"""
@fiete
November 12, 2020
"""

"""
INSTRUCTIONS TO RUN FROM COMMAND LINE:

python3.9 greedy_stochastic_search.py -path ../test_instances_ICEP_paper/test_3_heuristic -time_limit 600 -penalty 5000
"""

import pandas as pd  
import argparse
from matplotlib import pyplot as plt 
import numpy as np 
import os
import time

# import modules
from location import Location
from evacLocation import EvacLocation
from dock import Dock
from evacRes import EvacRes
from heuristic_phase1 import heuristic_phase_1
from heuristic_phase2 import heuristic_phase_2

# auxiliary functions for plotting
def create_best_cost_plot(best_cost_evo, path):
	"""
	A function to plot the best cost evolution
	"""
	updates = len(best_cost_evo)
	x = np.linspace(1, updates, updates)
	y = best_cost_evo

	plt.plot(x, y)
	plt.xlabel('Update index')
	plt.ylabel('Objective value')
	# plt.yscale('log') # change to logarithmic scale
	plt.savefig(os.path.join(path, 'solution/S_ICEP_greedy_best_objective_evolution.png'))
	plt.show()


def create_total_cost_plot(all_cost_evo, path):
	"""
	A function to plot all cost evolution
	"""
	x = np.linspace(0, len(all_cost_evo), len(all_cost_evo))
	print(x)
	y = all_cost_evo

	plt.plot(x, y)
	plt.xlabel('Iteration')
	plt.ylabel('Objective value')
	# plt.yscale('log') # change to logarithmic scale
	plt.savefig(os.path.join(path, 'solution/S_ICEP_greedy_all_objective_evolution.png'))
	plt.show()

def S_ICEP_heuristic(vessel_source, scenario_source, vessel_pos_source, 
                     is_locs_source, is_docks_source, mn_locs_source, mn_docks_source,
                     compat_source, distance_data, upper_time_limit, penalty):
    """
    A greedy search heuristic to find the optimal evacuation fleet
    """
    # initialize parameters
    possible_resource_no = len(vessel_source) 
    K = possible_resource_no * upper_time_limit
    
    # initialize the best cost
    best_cost = sum(scenario_source['Demand']) * penalty
    # print("Current best cost:", best_cost)
    n = 0

    # initialize a list for the best set of route plans
    best_route_set = None
    best_evacuation_times = None
    best_evacuee_numbers = None

    # initialize initial docks
    initial_docks = [Dock(vessel_pos_source.iloc[i,:], distance_data, compat_source) for i in range(vessel_pos_source.shape[0])]
    
    # initialize empty resource set
    resources = []
    not_in_resources = [EvacRes(vessel_source.iloc[i,:], initial_docks) for i in range(vessel_source.shape[0])]
    
    current_cost = best_cost - 1 # initialize

    # performance metric to record all cost propositions
    all_cost_evo = []
    all_cost_evo.append(best_cost)
    # performance metric to record the best cost evolution
    best_cost_evo = []
    best_cost_evo.append(best_cost)
    
    while (current_cost < best_cost) and (len(resources) < possible_resource_no):
        
        # update the best cost 
        best_cost = current_cost
        best_cost_evo.append(best_cost)

        save_previous = None # reset
        
        for a in not_in_resources:
        	if a not in resources:
	            if len(resources) >= n+1:
	                save_previous = resources[n]
	                resources[n] = a
	                indicator_first = False
	            else:
	                resources.append(a)
	                indicator_first = True


	            # iterate through all elements not in the resource set

	            # current proposed_cost
	            proposed_cost = 0

	            # add fixed cost component
	            for t in resources:
	                proposed_cost += 1/K * t.contract_cost

	            # print("Propose fixed cost:", proposed_cost)

	            # create a dataframe that records the route plans 
	            route_plans = []
	            not_evacuated = []
	            evacuation_times = []
	                
	            # run the algorithm
	            for j in scenario_source['Scenario'].unique():

	                # print(resources)
	                # initialize island and mainland location
	                island_locations = [EvacLocation(is_locs_source.iloc[i,:], scenario_source, j) for i in range(is_locs_source.shape[0])]
	                mainland_locations = [Location(mn_locs_source.iloc[i,:]) for i in range(mn_locs_source.shape[0])]

	                # initialize the docks
	                island_docks = [Dock(is_docks_source.iloc[i,:], distance_data, compat_source) for i in range(is_docks_source.shape[0])]
	                mainland_docks = [Dock(mn_docks_source.iloc[i,:], distance_data, compat_source) for i in range(mn_docks_source.shape[0])]

	                # initialize a fresh set of resources
	                resources_iteration = []
	                resource_names = [x.name for x in resources]
	                for unit in range(vessel_source.shape[0]):
	                    # print(vessel_source[vessel_source['Vessel_name'] == unit])
	                    if vessel_source.iloc[unit,0] in resource_names:
	                        resources_iteration.append(EvacRes(vessel_source.iloc[unit,:], initial_docks))
	                    else:
	                        pass


	                # run phase 1 of heuristic
	                route_details_initial, resources_iteration, island_locations, mainland_locations, island_docks, mainland_docks, t_evac, evacuees_left_behind = heuristic_phase_1(resources_iteration, 
	                                                                                                                                                 island_locations,                                                                                                                                            
	                                                                                                                                                 mainland_locations, 
	                                                                                                                                                 island_docks, 
	                                                                                                                                                 mainland_docks, 
	                                                                                                                                                 upper_time_limit)

	                # route_details_final, resources_iteration, island_locations, mainland_locations, island_docks, mainland_docks, max_route_time, evacuees_left_behind = heuristic_phase_1(resources_iteration, 
	                #                                                                                                                                  island_locations,                                                                                                                                            
	                #                                                                                                                                  mainland_locations, 
	                #                                                                                                                                  island_docks, 
	                #                                                                                                                                  mainland_docks, 
	                #                                                                                                                                  upper_time_limit)
	                     
	                # # run phase 2 of heuristic
	                route_details_final, resources_iteration, island_locations, mainland_locations, island_docks, mainland_docks, max_route_time, variable_operating_cost, evacuees_left_behind, fixed_cost = heuristic_phase_2(route_details_initial, resources_iteration, island_locations, mainland_locations, island_docks, mainland_docks, t_evac, upper_time_limit)

	                evacuees_left = 0
	                for k in island_locations:
	                    evacuees_left += k.current_evacuees
	                
	                operational_cost = 0
	                for k in resources_iteration:
	                	operational_cost += k.operating_cost * (k.current_route_time - k.time_to_availability)
	                scenario_cost = max_route_time + 1/K * operational_cost + penalty * evacuees_left_behind

	                scenario_prob = scenario_source['Probability'][scenario_source['Scenario'] == j].unique()[0]

	                proposed_cost += scenario_cost * scenario_prob

	                route_plans.append(route_details_final)
	                all_cost_evo.append(proposed_cost)
	                not_evacuated.append(evacuees_left_behind)
	                evacuation_times.append(max_route_time)

	                # print("Proposed scenario cost for", j, ":", scenario_cost)
	                # print("Proposed route time for", j, ":", max_route_time)
	                # print("Proposed evacuees left behind for", j, ":", evacuees_left_behind)
	                # print(route_details_final)
	                # print("")

	            # identify if the proposed cost is an improvement
	            if proposed_cost < current_cost:
	            	# print("Adding resource", resources[n].name, "to the resources set reduces the objective function from", current_cost, 'to', proposed_cost)
	            	current_cost = proposed_cost
	            	best_route_set = route_plans # update
	            	best_evacuation_times = evacuation_times
	            	best_evacuee_numbers = not_evacuated
	            	# not_in_resources.remove(a)
	            	# if indicator_first == False:
	             #        not_in_resources.append(save_previous)
	            	# print("Current resources in fleet:")
	            	# for i in resources:
	            	# 	print(i.name)

	            else:

	            	if save_previous == None:
	            		del resources[n] 
	            	else:
		            	# print("Proposed total cost:", proposed_cost)
		            	# print("Adding resource", resources[n].name, "to the resources set does not reduce the objective function.")
		            	resources[n] = save_previous

	        else:
	        	pass

        # print("Current best cost:", best_cost)

        # print("Current resources in fleet:")
        # for i in resources:
        #     print(i.name)

        # print("Current resources not in fleet:")
        # for i in not_in_resources:
        # 	print(i.name)
        # print("###################")
        # print("")

        # update n
        n += 1

    return(best_cost, best_cost_evo, all_cost_evo, best_route_set, not_evacuated, best_evacuation_times)


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument("-path", help="the path of the ICEP instance files")
	parser.add_argument("-penalty", type = int, help="the penalty value applied to every evacuee not evacuated.")
	parser.add_argument("-time_limit", type = float, help="the upper time limit for the evacuation plan.")

	args = parser.parse_args()

	# get directory path
	dirname = os.getcwd()

	rel_path = args.path
	path = os.path.join(dirname, rel_path)

	source = os.path.join(path, 'Input/')
	inc_source = os.path.join(path, 'Incidences/')

	# check if a solution directory exists
	if not os.path.exists(os.path.join(path, 'solution')):
		os.mkdir(os.path.join(path, "solution/"))

	# parse remaining arguments
	penalty = args.penalty
	time_limit = args.time_limit

	# read in data source files for nodes
	vessel_source = pd.read_csv(source + 'vessels.csv', index_col=False, 
	                            header=0, delimiter = ',', skipinitialspace=True)
	#print(vessel_source)
	trips_source = pd.read_csv(source + 'roundtrips.csv', index_col=False, 
	                           header=0, delimiter = ',', skipinitialspace=True)
	#print(trips_source)
	scenario_source = pd.read_csv(source + 'scenarios.csv', index_col = False,
	                              header=0, delimiter = ',', skipinitialspace=True)
	#print(scenarios_src)
	vessel_pos_source = pd.read_csv(source + 'initial vessel docks.csv', index_col = False,
	                              header=0, delimiter = ',', skipinitialspace=True)
	#print(vessel_pos_source)
	src_node_source = pd.read_csv(source + 'island source.csv', index_col=False, 
	                             header=0, delimiter = ',', skipinitialspace=True)
	#print(src_node_source)
	is_locs_source = pd.read_csv(source + 'island locations.csv', index_col=False, 
	                             header=0, delimiter = ',', skipinitialspace=True)
	#print(is_locs_source)
	is_docks_source = pd.read_csv(source + 'island docks.csv', index_col=False, 
	                              header=0, delimiter = ',', skipinitialspace=True)
	#print(is_docks_source)
	mn_locs_source = pd.read_csv(source + 'mainland locations.csv', index_col=False, 
	                             header=0, delimiter = ',', skipinitialspace=True)
	#print(mn_locs_source)
	mn_docks_source = pd.read_csv(source + 'mainland docks.csv', index_col=False, 
	                              header=0, delimiter = ',', skipinitialspace=True)
	#print(mn_docks_source)
	# vessel compatibility
	compat_source = pd.read_csv(source + 'vessel compatibility.csv', index_col=False, 
	                    header=0, delimiter = ',', skipinitialspace=True)
	#print(compat_source)

	# distances and compatibility
	distance_data = pd.read_csv(inc_source + 'distance matrix.csv', index_col=False, 
	                    header=0, delimiter = ',', skipinitialspace=True)
	#print(distance_source)	

	print("Starting greedy stochastic search for optimal solution to S-ICEP...")
	print("")

	start = time.time()

	best_cost, best_cost_evo, all_cost_evo, best_route_set, not_evacuated, best_evacuation_times = S_ICEP_heuristic(vessel_source, scenario_source, vessel_pos_source, 
                     is_locs_source, is_docks_source, mn_locs_source, mn_docks_source,
                     compat_source, distance_data, time_limit, penalty)

	end = time.time()
	run_time = end - start

	print('Time to solution:', run_time)

	print("************************************")
	print("The best objective value obtained:", best_cost[0])
	print("Run time to find solution:", run_time)
	print("The best set of route plans obtained:")
	for i in range(len(best_route_set)):
		print("Scenario", i+1, ":")
		print("Population not evacuated:")
		print(not_evacuated[i][0])
		print("Evacuation time:")
		print(best_evacuation_times[i])
		print(best_route_set[i])
		best_route_set[i].to_csv(os.path.join(path, 'solution/Greedy_S_ICEP_best_route_plan_scenario_') + str(i+1) + ".csv")

	# write a performance file
	performance_metrics = open(os.path.join(path, "solution/Greedy_S_ICEP_solution_metrics_.txt"),"w+")
	performance_metrics.write("Input parameters:\n")
	performance_metrics.write("Penalty: " + str(penalty) + "\n")
	performance_metrics.write("Upper time limit: " + str(time_limit) + "\n")
	performance_metrics.write("Algorithm run time: " + str(run_time) + "\n")
	performance_metrics.write("")
	performance_metrics.write("Results: \n")
	for i in range(len(best_route_set)):
		performance_metrics.write("Scenario " + str(i+1) + ": \n")
		performance_metrics.write("Population not evacuated: " + str(not_evacuated[i]) + "\n")
		performance_metrics.write("Evacuation time: " + str(best_evacuation_times[i]) + "\n")
	performance_metrics.close()

	# generate the evolution plots
	# create_best_cost_plot(best_cost_evo, path)
	# create_total_cost_plot(all_cost_evo, path)

if __name__ == "__main__":
	main()


