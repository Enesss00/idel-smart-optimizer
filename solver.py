from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import logging

# Configuration du logging pour le débuggage en prod
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RouteSolver:
    def __init__(self, time_matrix: list, time_windows: list, num_vehicles: int = 1, depot: int = 0):
        self.time_matrix = time_matrix
        self.time_windows = time_windows
        self.num_vehicles = num_vehicles
        self.depot = depot

    def solve(self):
        """
        Solves the VRPTW and returns the optimized sequence of nodes.
        Returns: List[int] or None if no solution is found.
        """
        # 1. Create Routing Index Manager
        manager = pywrapcp.RoutingIndexManager(len(self.time_matrix), self.num_vehicles, self.depot)
        routing = pywrapcp.RoutingModel(manager)

        # 2. Define cost of each arc (Travel Time)
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self.time_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # 3. Add Time Windows Constraint
        time_dimension_name = 'Time'
        routing.AddDimension(
            transit_callback_index,
            30,  # Max waiting time at a location
            1440, # Max total time (24h in minutes)
            False,
            time_dimension_name
        )
        time_dimension = routing.GetDimensionOrDie(time_dimension_name)

        for location_idx, (start, end) in enumerate(self.time_windows):
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(start, end)

        # 4. Search Parameters (Heuristics for fast solving)
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        # 5. Solve
        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            logger.warning("Solver failed to find a valid route.")
            return None

        return self._extract_route(manager, routing, solution)

    def _extract_route(self, manager, routing, solution):
        """Helper to format the solution into a simple list of node IDs."""
        route = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index)) # Add depot return
        return route