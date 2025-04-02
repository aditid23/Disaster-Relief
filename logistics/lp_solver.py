from pulp import LpMinimize, LpProblem, LpVariable, lpSum, LpStatus

def solve_transportation_problem(warehouses, areas, costs):
    problem = LpProblem("TransportationProblem", LpMinimize)

    allocation = {
        (w, a): LpVariable(f"x_{w}_{a}", lowBound=0, cat='Continuous')  
        for w in warehouses for a in areas
    }

    problem += lpSum(allocation[w, a] * costs[(w, a)] for w, a in allocation), "Total Cost"

    for w in warehouses:
        problem += lpSum(allocation[w, a] for a in areas) <= warehouses[w], f"Supply_{w}"

    for a in areas:
        problem += lpSum(allocation[w, a] for w in warehouses) >= areas[a], f"Demand_{a}"

    problem.solve()

    solution = {
        (w, a): int(var.varValue) 
        for (w, a), var in allocation.items() 
        if var.varValue is not None and var.varValue > 0
    }

    return solution
