"""
@fiete
November 12, 2020
"""

"""
INSTRUCTIONS TO RUN FROM COMMAND LINE:

python3.9 greedy_deterministic_search.py -path ../test_instances_ICEP_paper/test_3_heuristic -time_limit 600 -penalty 5000 -scenario 'Scenario 1'
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


def D_ICEP_heuristic(vessel_source, scenario_source, vessel_pos_source, 
                     is_locs_source, is_docks_source, mn_locs_source, mn_docks_source,
                     compat_source, distance_data, upper_time_limit, penalty, scenario):
    """
    A greedy search heuristic to find the optimal route plan for a deterministic scenario
    """
    # initialize island and mainland location
    island_locations = [EvacLocation(is_locs_source.iloc[i,:], scenario_source, scenario) for i in range(is_locs_source.shape[0])]
    mainland_locations = [Location(mn_locs_source.iloc[i,:]) for i in range(mn_locs_source.shape[0])]

    # initialize the docks
    island_docks = [Dock(is_docks_source.iloc[i,:], distance_data, compat_source) for i in range(is_docks_source.shape[0])]
    mainland_docks = [Dock(mn_docks_source.iloc[i,:], distance_data, compat_source) for i in range(mn_docks_source.shape[0])]
    initial_docks = [Dock(vessel_pos_source.iloc[i,:], distance_data, compat_source) for i in range(vessel_pos_source.shape[0])]
    
    # initialize resource set
    resources = [EvacRes(vessel_source.iloc[i,:], initial_docks) for i in range(vessel_source.shape[0])]

    # run phase 1 of heuristic
    route_details_initial, resources_iteration, island_locations, mainland_locations, island_docks, mainland_docks, t_evac, evacuees_left_behind = heuristic_phase_1(resources, 
                                                                                                                                     island_locations,                                                                                                                                            
                                                                                                                                     mainland_locations, 
                                                                                                                                     island_docks, 
                                                                                                                                     mainland_docks, 
                                                                                                                                     upper_time_limit)

    # run phase 2 of heuristic
    route_details_final, resources_iteration, island_locations, mainland_locations, island_docks, mainland_docks, max_route_time, variable_operating_cost, evacuees_left_behind, fixed_cost = heuristic_phase_2(route_details_initial, resources_iteration, island_locations, mainland_locations, island_docks, mainland_docks, t_evac, upper_time_limit)

    # route_details_final, resources_iteration, island_locations, mainland_locations, island_docks, mainland_docks, max_route_time, evacuees_left_behind = heuristic_phase_1(resources, 
    #                                                                                                                                  island_locations,                                                                                                                                            
    #                                                                                                                                  mainland_locations, 
    #                                                                                                                                  island_docks, 
    #                                                                                                                                  mainland_docks, 
    #                                                                                                                                  upper_time_limit)
         

    return(route_details_final, max_route_time, evacuees_left_behind)


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument("-path", help="the path of the ICEP instance files")
	parser.add_argument("-penalty", type = int, help="the penalty value applied to every evacuee not evacuated.")
	parser.add_argument("-time_limit", type = float, help="the upper time limit for the evacuation plan.")
	parser.add_argument("-scenario", type = str, help="the scenario name for the test instance.")

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
	scenario = args.scenario

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

	print("Starting greedy deterministic search for a solution to D-ICEP...")
	print("")

	start = time.time()

	route_details_final, max_route_time, evacuees_left_behind = D_ICEP_heuristic(vessel_source, scenario_source, vessel_pos_source, 
                     is_locs_source, is_docks_source, mn_locs_source, mn_docks_source,
                     compat_source, distance_data, time_limit, penalty, scenario)

	end = time.time()
	run_time = end - start

	print('Time to solution:', run_time)

	print('Objective value:', max_route_time + penalty * evacuees_left_behind)

	print('Total evacuees evacuated with final solution:', sum(route_details_final['evacuees']), 'in', max_route_time, 'minutes')
	print('Evacuees left behind:', evacuees_left_behind)

	print(route_details_final)
	route_details_final.to_csv(os.path.join(path, 'solution/Greedy_D_ICEP_best_route_plan_scenario_') + str(scenario) + ".csv")

if __name__ == "__main__":
	main()


