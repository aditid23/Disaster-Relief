from django.shortcuts import render, redirect
from .lp_solver import solve_transportation_problem  

def input_data(request):
    if request.method == 'POST':
        print("✅ Received POST Request")
        print("📌 POST Data:", request.POST)  

        warehouse_names = request.POST.getlist('warehouse_name[]')
        warehouse_supplies = request.POST.getlist('warehouse_supply[]')
        area_names = request.POST.getlist('area_name[]')
        area_demands = request.POST.getlist('area_demand[]')
        from_warehouses = request.POST.getlist('from_warehouse[]')
        to_areas = request.POST.getlist('to_area[]')
        transport_costs = request.POST.getlist('transport_cost[]')

        # Convert input lists to dictionaries
        warehouses = {name.strip(): int(supply) for name, supply in zip(warehouse_names, warehouse_supplies)}
        areas = {name.strip(): int(demand) for name, demand in zip(area_names, area_demands)}
        costs = {(w.strip(), a.strip()): int(c) for w, a, c in zip(from_warehouses, to_areas, transport_costs)}

        # Calculate total supply and demand
        total_supply = sum(warehouses.values())
        total_demand = sum(areas.values())

        print(f"📊 Total Supply: {total_supply}, Total Demand: {total_demand}")

        warning_message = None  # Initialize warning message

        # If supply is less than demand, adjust the demand proportionally
        if total_supply < total_demand:
            print("⚠️ Supply is less than demand. Adjusting demand proportionally.")

            # Adjust demand proportionally
            adjustment_factor = total_supply / total_demand
            areas = {area: int(demand * adjustment_factor) for area, demand in areas.items()}

            warning_message = "Total supply is less than demand. Demand has been adjusted proportionally."

            print(f"🔄 Adjusted Demand: {areas}")

        # Solve the transportation problem
        try:
            solver_output = solve_transportation_problem(warehouses, areas, costs)

            print("📌 Solver Output:", solver_output)  # Debugging

            # Ensure solution keys are formatted correctly
            solution = {f"{w} → {a}": allocated_units for (w, a), allocated_units in solver_output.items()}

        except Exception as e:
            print("❌ LP Solver Error:", str(e))
            return render(request, 'input.html', {'error_message': f"Solver error: {str(e)}"})

        # Compute total cost per city and total allocation per city
        city_costs = {}  
        total_cost = 0

        for (warehouse, area), allocated_units in solver_output.items():
            cost_per_unit = costs.get((warehouse, area), 0)
            total_city_cost = allocated_units * cost_per_unit
            city_costs[area] = city_costs.get(area, 0) + total_city_cost
            total_cost += total_city_cost

        # Save solution and costs in session and redirect to results
        request.session['solution'] = solution
        request.session['city_costs'] = city_costs
        request.session['total_cost'] = total_cost
        request.session['warning_message'] = warning_message  # Pass warning message
        return redirect('results_page')

    return render(request, 'input.html')

def results_page(request):
    # Retrieve solution and costs from session
    solution = request.session.get('solution', {})
    city_costs = request.session.get('city_costs', {})
    total_cost = request.session.get('total_cost', 0)

    print("📌 Raw Solution from Solver:", solution)

    if not solution:
        print("⚠️ No solution found in session.")
        return render(request, 'results.html', {'error': "No solution available. Please enter input again."})

    processed_solution = []
    city_units = {}  # Dictionary to store total units per city
    total_units_supplied = 0  # Total units across all routes

    for route, allocation in solution.items():
        print(f"🔹 Route Key: {route} | Type: {type(route)}")  
        print(f"🔹 Allocation Value: {allocation}")

        try:
            if isinstance(route, str) and " → " in route:
                warehouse, area = route.split(" → ")
            else:
                print(f"❌ Invalid route format: {route}")
                continue  # Skip invalid entries

            processed_solution.append({'warehouse': warehouse, 'area': area, 'allocation': allocation})

            # Track total units per city
            city_units[area] = city_units.get(area, 0) + allocation
            total_units_supplied += allocation  # Sum all allocations

        except ValueError as e:
            print(f"❌ Unpacking Error: {e} | Route: {route}")

    # Sort cities alphabetically before passing to template
    sorted_cities = sorted(city_units.keys())

    print("✅ Processed Solution (To Template):", processed_solution)
    print("📦 Total Units Per City:", city_units)
    print("💰 Total Cost of Transportation:", total_cost)

    return render(request, 'results.html', {
        'solution': processed_solution,
        'city_units': city_units,
        'city_costs': city_costs,
        'sorted_cities': sorted_cities,  # Sorted city names
        'total_units_supplied': total_units_supplied,
        'total_cost': total_cost
    })
