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
        return self.name

class TransportationCost(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    affected_area = models.ForeignKey(AffectedArea, on_delete=models.CASCADE)  # Ensure the correct field name
    cost = models.FloatField()

    def __str__(self):
        return f"{self.warehouse} → {self.affected_area} : {self.cost}"
