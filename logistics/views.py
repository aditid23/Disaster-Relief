import json
import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Sum, FloatField
from django.db.models.functions import Coalesce, Cast

from .lp_solver import solve_transportation_problem  
from .models import Warehouse, AffectedArea, TransportationCost, AllocationResult, OptimizationResult, PriorityAllocation


# -------------------- Home Redirect --------------------
def home_redirect(request):
    return redirect('input_page')


# -------------------- Input Data Handler --------------------
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
        actual_demands = areas.copy()

        if total_supply < total_demand:
            adjustment_factor = total_supply / total_demand
            areas = {area: int(demand * adjustment_factor) for area, demand in areas.items()}
            warning_message = "⚠ Total supply is less than demand. Demand has been adjusted proportionally."

        try:
            solver_output = solve_transportation_problem(warehouses, areas, costs)
            solution = {f"{w} → {a}": allocated_units for (w, a), allocated_units in solver_output.items()}

            # ✅ Save allocation results to the DB
            AllocationResult.objects.all().delete()

            for (warehouse, area), units in solver_output.items():
                cost_per_unit = costs.get((warehouse, area), 0)
                AllocationResult.objects.create(
                warehouse=warehouse,
                area=area,
                allocated_units=units,
                cost=cost_per_unit
                )


        except Exception as e:
            return render(request, 'input.html', {'error_message': f"Solver error: {str(e)}"})

        city_costs = {}  
        total_cost = 0
        total_units_supplied = sum(solver_output.values())
        print("Solver output:", solver_output)
        for (warehouse, area), allocated_units in solver_output.items():
            cost_per_unit = costs.get((warehouse, area), 0)
            total_city_cost = allocated_units * cost_per_unit
            city_costs[area] = city_costs.get(area, 0) + total_city_cost
            total_cost += total_city_cost
        print("AllocationResult count after saving:", AllocationResult.objects.count())
        fulfillment_rate = (total_units_supplied / total_demand) * 100 if total_demand else 0

        save_optimization_results(fulfillment_rate, total_cost, total_units_supplied, {})

        request.session['solution'] = solution
        request.session['city_costs'] = city_costs
        request.session['total_cost'] = total_cost
        request.session['warning_message'] = warning_message  
        request.session['actual_demands'] = actual_demands  

        return redirect('results_page')

    return render(request, 'input.html')

# -------------------- Results Page --------------------
def results_page(request):
    solution = request.session.get('solution', {})
    city_costs = request.session.get('city_costs', {})
    total_cost = request.session.get('total_cost', 0)
    actual_demands = request.session.get('actual_demands', {})

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
        'total_cost': total_cost,
        'actual_demands': actual_demands  
    })


# -------------------- Dashboard Page --------------------
def dashboard_page(request):
    aggregated_result = OptimizationResult.objects.aggregate(
        total_fulfillment_rate=Coalesce(Sum(Cast('fulfillment_rate', FloatField())), 0.0),
        total_cost=Coalesce(Sum(Cast('total_cost', FloatField())), 0.0),
        total_units=Coalesce(Sum(Cast('total_units', FloatField())), 0.0)
    )

    priority_qs = PriorityAllocation.objects.values('priority').annotate(total_units=Sum('units'))
    priority_data = list(priority_qs)

    context = {
        "fulfillment_rate": aggregated_result["total_fulfillment_rate"],
        "total_cost": aggregated_result["total_cost"],
        "total_units": aggregated_result["total_units"],
        "priority_data": json.dumps(priority_data)
    }

    return render(request, "dashboard.html", context)


# -------------------- Save Optimization Results --------------------
def save_optimization_results(fulfillment_rate, total_cost, total_units, priority_allocations):
    session = OptimizationResult.objects.create(
        fulfillment_rate=fulfillment_rate,
        total_cost=total_cost,
        total_units=total_units
    )

    for priority, units in priority_allocations.items():
        PriorityAllocation.objects.create(session=session, priority=priority, units=units)


# -------------------- Static Dashboard Mock View --------------------
def dashboard_view(request):
    priority_data = [
        {"priority": "High", "total_units": 150},
        {"priority": "Medium", "total_units": 100},
        {"priority": "Low", "total_units": 50}
    ]
    return render(request, "dashboard.html", {
        "priority_data_json": json.dumps(priority_data),
        "total_cost": 10000,
        "total_units": 300,
        "fulfillment_rate": 85
    })


# -------------------- Export CSV --------------------
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="allocation_results.csv"'

    writer = csv.writer(response)
    writer.writerow(['Warehouse', 'Area', 'Allocated Units', 'Cost'])

    results = AllocationResult.objects.all()
    for result in results:
        writer.writerow([result.warehouse, result.area, result.allocated_units, result.cost])

    return response

