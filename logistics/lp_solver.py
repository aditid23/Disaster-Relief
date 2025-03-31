from pulp import LpMinimize, LpProblem, LpVariable, lpSum, LpStatus

def solve_transportation_problem(warehouses, areas, costs):
    # Define the problem
    problem = LpProblem("TransportationProblem", LpMinimize)

    # Define decision variables
    allocation = {
        (w, a): LpVariable(f"x_{w}_{a}", lowBound=0, cat='Continuous')  
        for w in warehouses for a in areas
    }

    # Objective function: Minimize transportation cost
    problem += lpSum(allocation[w, a] * costs[(w, a)] for w, a in allocation), "Total Cost"

    # Constraints: Supply constraints
    for w in warehouses:
        problem += lpSum(allocation[w, a] for a in areas) <= warehouses[w], f"Supply_{w}"

    # Constraints: Demand constraints
    for a in areas:
        problem += lpSum(allocation[w, a] for w in warehouses) >= areas[a], f"Demand_{a}"

    # Solve the problem
    problem.solve()

    print("Solver Status:", LpStatus[problem.status])  # Debugging

    # Extract results
    solution = {}
    for (w, a), var in allocation.items():
        if var.varValue is not None and var.varValue > 0:  # Avoid zero allocations
            solution[(w, a)] = int(var.varValue)  # Ensure integer values

    print("Final Solution:", solution)  # Debugging
    return solution
