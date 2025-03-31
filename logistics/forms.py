from django import forms
from .models import Warehouse, AffectedArea, TransportationCost

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'supply']

class AffectedAreaForm(forms.ModelForm):
    class Meta:
        model = AffectedArea
        fields = ['name', 'demand']

class TransportationCostForm(forms.ModelForm):
    class Meta:
        model = TransportationCost
        fields = ['warehouse', 'affected_area', 'cost']
