from django.db import models


class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    supply = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class AffectedArea(models.Model):
    name = models.CharField(max_length=100)
    demand = models.PositiveIntegerField()

    def __str__(self):
        return self.name  # Removed the priority reference

class TransportationCost(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    affected_area = models.ForeignKey(AffectedArea, on_delete=models.CASCADE)
    cost = models.FloatField()

    def __str__(self):
        return f"{self.warehouse} → {self.affected_area} : {self.cost}"

class AllocationResult(models.Model):
    warehouse = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    allocated_units = models.PositiveIntegerField()
    cost = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.warehouse} → {self.area}: {self.allocated_units} units"


from django.db import models
from django.utils.timezone import now

class OptimizationResult(models.Model):
    timestamp = models.DateTimeField(default=now)
    fulfillment_rate = models.FloatField()
    total_cost = models.FloatField()
    total_units = models.IntegerField()
