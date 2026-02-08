from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('cold-caller/', views.cold_caller_dashboard, name='cold_caller_dashboard'),
    path('cold-caller/add/', views.add_lead, name='add_lead'),
    path('cold-caller/edit/<int:pk>/', views.edit_lead, name='edit_lead'),
    path('cold-caller/delete/<int:pk>/', views.delete_lead, name='delete_lead'),
    path('sales-closer/', views.SalesCloserDashboardView.as_view(), name='sales_closer_dashboard'),
    path('sales-closer/mark-won/<int:pk>/', views.mark_won, name='mark_won'),
    path('sales-closer/mark-lost/<int:pk>/', views.mark_lost, name='mark_lost'),
    path('sales-closer/onboard/', views.sales_closer_onboard, name='sales_closer_onboard'),
    path('filter/', views.filter_leads, name='filter'),
]
