from django.urls import path
from .views import input_data, results_page

urlpatterns = [
    path('', input_data, name='input_page'),
    path('results/', results_page, name='results_page'),
]
    