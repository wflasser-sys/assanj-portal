"""
URL configuration for projects app.
"""

from django.urls import path
from .views import (
    CreateProjectView,
    FetcherProjectListView,
    FetcherProjectDetailView,
    AdminProjectListView,
    AdminProjectDetailView,
    AdminAssignDeveloperView,
    AdminPaymentReleaseView,
    AdminAdvanceStageView,
    AdminRevertStageView,
    AdminUpdateFinancialsView,
    AdminUpdatePreviewView,
    DeveloperProjectListView,
    DeveloperProjectDetailView,
    DeveloperUpdateStatusView,
    execution_submit_update,
    my_earnings,
)

urlpatterns = [
    path(
        "projects/fetcher/add/",
        CreateProjectView.as_view(),
        name="fetcher_add_project"
    ),
    path('fetcher/', FetcherProjectListView.as_view(), name='fetcher_projects'),
    path('fetcher/<int:pk>/', FetcherProjectDetailView.as_view(), name='fetcher_project_detail'),
    
    path('admin-panel/', AdminProjectListView.as_view(), name='admin_projects'),
    path('admin-panel/<int:pk>/', AdminProjectDetailView.as_view(), name='admin_project_detail'),
    path('admin-panel/<int:pk>/assign/', AdminAssignDeveloperView.as_view(), name='admin_assign'),
    path('admin-panel/<int:pk>/release/', AdminPaymentReleaseView.as_view(), name='admin_payment_release'),
    path('admin-panel/<int:pk>/advance-stage/', AdminAdvanceStageView.as_view(), name='admin_advance_stage'),
    path('admin-panel/<int:pk>/revert-stage/', AdminRevertStageView.as_view(), name='admin_revert_stage'),
    path('admin-panel/<int:pk>/financials/', AdminUpdateFinancialsView.as_view(), name='admin_update_financials'),
    path('admin-panel/<int:pk>/preview/', AdminUpdatePreviewView.as_view(), name='admin_update_preview'),
    path('admin-panel/assign/<int:pk>/', AdminAssignDeveloperView.as_view(), name='admin_assign'),
    path('admin-panel/payment-release/<int:pk>/', AdminPaymentReleaseView.as_view(), name='admin_payment_release'),
    
    path('developer/', DeveloperProjectListView.as_view(), name='developer_projects'),
    path('developer/<int:pk>/', DeveloperProjectDetailView.as_view(), name='developer_project_detail'),
    path('execution/<int:pk>/add-update/', execution_submit_update, name='execution_submit_update'),
    path('developer/update/<int:pk>/', DeveloperUpdateStatusView.as_view(), name='developer_update_status'),
    path('my-earnings/', my_earnings, name='my_earnings'),
]
