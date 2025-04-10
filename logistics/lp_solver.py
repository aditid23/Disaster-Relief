def solve_transportation_problem(warehouses, areas, costs, priorities=None):
    from pulp import LpMinimize, LpProblem, LpVariable, lpSum

    problem = LpProblem("TransportationProblem", LpMinimize)

    allocation = {
        (w, a): LpVariable(f"x_{w}_{a}", lowBound=0, cat='Continuous')  
        for w in warehouses for a in areas
    }

    if priorities:
        max_priority = max(priorities.values())
        priority_weights = {a: (max_priority + 1 - p) for a, p in priorities.items()}
        weighted_costs = {
            (w, a): costs.get((w, a), 0) * priority_weights.get(a, 1)
            for (w, a) in allocation
        }
        problem += lpSum(allocation[w, a] * weighted_costs[(w, a)] for (w, a) in allocation), "PriorityWeightedCost"
    else:
        problem += lpSum(allocation[w, a] * costs[(w, a)] for w, a in allocation), "TotalCost"

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
