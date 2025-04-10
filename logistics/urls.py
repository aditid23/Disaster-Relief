from django.urls import path
from .views import input_data, results_page, dashboard_page, home_redirect, export_csv

urlpatterns = [
    path('', home_redirect),
    path('input/', input_data, name='input_page'),
    path('results/', results_page, name='results_page'),
    path('dashboard/', dashboard_page, name='go_to_dashboard'),
    path('export-csv/', export_csv, name='export_csv'),
]