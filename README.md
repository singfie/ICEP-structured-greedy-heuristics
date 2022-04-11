# ICEP Greedy Structured Heuristics
Structural heuristics for the deterministic (D-ICEP) and planning (S-ICEP) version of the Isolated Community Evacuation Problem (ICEP)

The D-ICEP represents the base version of the ICEP with deterministic data. Due to the high complexity of the problem, large instances are difficult to solve. The structural heuristics (phase 1 and phase 2) allow for quicker solution times in comparison to commercial solvers (see the repository on https://github.com/singfie/ICEP-exact-implementation for an exact implementation with a commercial solver).

The S-ICEP is a modified version of the D-ICEP for planning purposes. It adds a two-stage stochastic model structure with recourse. The scenario-independent first stage of the model includes the decision on an optimal evacuation resource fleet. The scenario-dependent second stage optimizes the evacuation route plan for a given evacuation scenario. The structure-based greedy search heuristics in this package allow for also solving the S-ICEP more quickly than with the D-ICEP. 

More information on the algorithms and the model itself can be found in the paper corresponding to this package: 
Krutein, K. F. & Goochild, A. The Isolated Community Evacuation Problem with Mixed Integer Programming. Transportation Research Part E: Logistics & Transportation Review. (2022) Volume: tbd

# File descriptions

# dock.py
This file implements an instance of an evacuation dock (evacuation pick-up and drop-off points)

# location.py
This file implements an instance of a location

# evacLocation.py
This file implements an instance of an evacuation location, and forms a sub-class of "location.py"

# evacRes.py
This file implements an evacuation resource. 

# generate_outputs.py
This file prints outputs from the best solution of the MP-BRKGA, in the form of a route plan. 

# heuristic_phase1.py
This file implements phase 1 of the structure-based heuristic for the D-ICEP used in the paper mentioned above. 

# heuristic_phase2.py
This file implements phase 2 of the structure-based heuristic for the D-ICEP used in the paper mentioned above.

# greedy_deterministic_search.py
This file implements the greedy wrapper around heuristic phase 1 and phase 2, that represents the entire heuristic for the D-ICEP.

# greedy_stochastic_search.py
This file represents a stochastic search method for the S-ICEP that aims to test all possible resource combinations

# greedy_simple_stochastic_search.py
This file represents a stochastic search method for the S-ICEP that simplifies "greedy_stochastic_search.py" and always updates the solution as soon as an improvement can be found, before looking for a better solution.
