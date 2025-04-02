from django.shortcuts import render, redirect
from .lp_solver import solve_transportation_problem  

def input_data(request):
    if request.method == 'POST':
        warehouse_names = request.POST.getlist('warehouse_name[]')
        warehouse_supplies = request.POST.getlist('warehouse_supply[]')
        area_names = request.POST.getlist('area_name[]')
        area_demands = request.POST.getlist('area_demand[]')
        from_warehouses = request.POST.getlist('from_warehouse[]')
        to_areas = request.POST.getlist('to_area[]')
        transport_costs = request.POST.getlist('transport_cost[]')

        warehouses = {name.strip(): int(supply) for name, supply in zip(warehouse_names, warehouse_supplies)}
        areas = {name.strip(): int(demand) for name, demand in zip(area_names, area_demands)}
        costs = {(w.strip(), a.strip()): int(c) for w, a, c in zip(from_warehouses, to_areas, transport_costs)}

        total_supply = sum(warehouses.values())
        total_demand = sum(areas.values())

        warning_message = None  

        if total_supply < total_demand:
            adjustment_factor = total_supply / total_demand
            areas = {area: int(demand * adjustment_factor) for area, demand in areas.items()}
            warning_message = "Total supply is less than demand. Demand has been adjusted proportionally."

        try:
            solver_output = solve_transportation_problem(warehouses, areas, costs)
            solution = {f"{w} → {a}": allocated_units for (w, a), allocated_units in solver_output.items()}
        except Exception as e:
            return render(request, 'input.html', {'error_message': f"Solver error: {str(e)}"})

        city_costs = {}  
        total_cost = 0

        for (warehouse, area), allocated_units in solver_output.items():
            cost_per_unit = costs.get((warehouse, area), 0)
            total_city_cost = allocated_units * cost_per_unit
            city_costs[area] = city_costs.get(area, 0) + total_city_cost
            total_cost += total_city_cost

        request.session['solution'] = solution
        request.session['city_costs'] = city_costs
        request.session['total_cost'] = total_cost
        request.session['warning_message'] = warning_message  
        return redirect('results_page')

    return render(request, 'input.html')

def results_page(request):
    solution = request.session.get('solution', {})
    city_costs = request.session.get('city_costs', {})
    total_cost = request.session.get('total_cost', 0)

    if not solution:
        return render(request, 'results.html', {'error': "No solution available. Please enter input again."})

    processed_solution = []
    city_units = {}  
    total_units_supplied = 0  

    for route, allocation in solution.items():
        try:
            if isinstance(route, str) and " → " in route:
                warehouse, area = route.split(" → ")
            else:
                continue  

            processed_solution.append({'warehouse': warehouse, 'area': area, 'allocation': allocation})
            city_units[area] = city_units.get(area, 0) + allocation
            total_units_supplied += allocation  
        except ValueError:
            continue  

    sorted_cities = sorted(city_units.keys())

    return render(request, 'results.html', {
        'solution': processed_solution,
        'city_units': city_units,
        'city_costs': city_costs,
        'sorted_cities': sorted_cities,  
        'total_units_supplied': total_units_supplied,
        'total_cost': total_cost
    })
